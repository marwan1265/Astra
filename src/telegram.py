# This file will contain the code for handling Telegram interactions,
# including the telegram_handler node for the LangGraph agent.

import os
import asyncio
import logging
import json
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from http import HTTPStatus
from contextlib import asynccontextmanager
import aiosqlite
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.config import RunnableConfig
from langgraph.prebuilt import ToolNode

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from src.state import AgentState
from src.tools import list_calendar_events
from src.prompts import SecretaryPrompts

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YOUR_CHAT_ID = os.getenv("YOUR_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- Sanity Check for Environment Variables ---
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set.")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL environment variable not set. Please check your .env file.")
logger.info(f"Read WEBHOOK_URL from environment: {WEBHOOK_URL}")
# --- End Sanity Check ---

# --- LangGraph Setup ---

# Initialize the LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-06-05", google_api_key=os.getenv("GOOGLE_API_KEY"))

# Define the tools
tools = [list_calendar_events]
tool_node = ToolNode(tools)

# Bind the tools to the LLM
llm_with_tools = llm.bind_tools(tools)

def should_continue(state: AgentState):
    """Router logic to decide whether to continue or end the conversation."""
    if not state.messages:
        return "end"
    
    last_message = state.messages[-1]
    
    # Handle AIMessage objects
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "continue"
    
    # Handle dict format
    if isinstance(last_message, dict) and "tool_calls" in last_message and last_message["tool_calls"]:
        return "continue"
    
    return "end"

async def agent_node(state: AgentState, config: RunnableConfig):
    """The main agent node that calls the LLM."""
    prepared: list = []
    
    # Get the dynamic system prompt
    system_message = SecretaryPrompts.get_system_prompt()
    
    prepared.append(HumanMessage(content=system_message))
    
    # Logic to find the tool name for any tool messages
    tool_call_map = {}
    for m in state.messages:
        if isinstance(m, AIMessage) and m.tool_calls:
            for tc in m.tool_calls:
                tool_call_map[tc['id']] = tc['name']

    for m in state.messages:
        if isinstance(m, (HumanMessage, AIMessage, ToolMessage)):
            # If we get a tool message from the calendar, use our custom prompter
            if isinstance(m, ToolMessage):
                tool_name = tool_call_map.get(m.tool_call_id)
                if tool_name == 'list_calendar_events':
                    try:
                        events = json.loads(m.content)
                        summary_prompt = SecretaryPrompts.summarize_calendar_events(events)
                        # Replace the raw tool output with our detailed prompt
                        m.content = summary_prompt
                    except (json.JSONDecodeError, TypeError):
                        # If content isn't valid JSON, just pass it along
                        pass
            
            # For AIMessage: include if it has content OR tool calls
            if isinstance(m, AIMessage):
                if (m.content and m.content.strip()) or (hasattr(m, 'tool_calls') and m.tool_calls):
                    prepared.append(m)
            # For other message types: only include if they have content
            elif hasattr(m, 'content') and m.content and m.content.strip():
                prepared.append(m)
        elif isinstance(m, dict):
            m_type = m.get("type") or m.get("role")
            content = m.get("content", "")
            
            # Skip if content is None, empty, or just whitespace
            if not content or not str(content).strip():
                continue
                
            content = str(content).strip()
                
            if m_type in ("human", "user"):
                prepared.append(HumanMessage(content=content))
            elif m_type in ("ai", "assistant"):
                # Handle tool calls if present
                tool_calls = m.get("tool_calls", [])
                if tool_calls:
                    prepared.append(AIMessage(content=content, tool_calls=tool_calls))
                else:
                    prepared.append(AIMessage(content=content))
            elif m_type == "tool":
                tool_call_id = m.get("tool_call_id", "")
                content = m.get("content", "")
                
                tool_name = tool_call_map.get(tool_call_id)
                if tool_name == 'list_calendar_events':
                    try:
                        events = json.loads(content)
                        summary_prompt = SecretaryPrompts.summarize_calendar_events(events)
                        content = summary_prompt # Replace content
                    except (json.JSONDecodeError, TypeError):
                        pass

                if tool_call_id:  # Only add if we have a valid tool_call_id
                    prepared.append(ToolMessage(content=content, tool_call_id=tool_call_id))

    if len(prepared) <= 1:  # Only system message, add fallback
        prepared.append(HumanMessage(content="Hello"))

    response = await llm_with_tools.ainvoke(prepared, config=config)
    return {"messages": [response]}

# Define the graph structure, but don't compile it yet.
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"continue": "tools", "end": END},
)

workflow.add_edge("tools", "agent")

# The compiled graph object, will be initialized in the lifespan.
agent_executor = None

# --- Telegram Bot and FastAPI Setup ---

ptb_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text("Hello! I am your secretary agent.")

async def unauthorized_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles messages from unauthorized users."""
    await update.message.reply_text("Unauthorized access.")

ptb_app.add_handler(CommandHandler("start", start))

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process incoming messages by invoking the LangGraph agent."""
    if str(update.message.chat_id) != YOUR_CHAT_ID:
        await unauthorized_user(update, context)
        return

    config: RunnableConfig = {
        "configurable": {
            "thread_id": str(update.message.chat_id),
        }
    }
    
    initial_state = {"messages": [{"type": "human", "content": update.message.text}]}
    
    # Define a background task to stream the response
    async def stream_and_respond():
        final_response = ""
        async for chunk in agent_executor.astream(initial_state, config=config):
            # The final response is in the 'agent' node's output
            if "agent" in chunk:
                agent_response = chunk["agent"]["messages"][-1]
                
                # Accumulate content deltas instead of overwriting
                delta = getattr(agent_response, "content", "") or ""
                if delta:
                    final_response += delta
        
        if final_response.strip():
            await update.message.reply_text(final_response)
        else:
            # Fallback in case no content is generated
            await update.message.reply_text("Sorry, I couldn't generate a response.")

    # Run the streaming task in the background
    asyncio.create_task(stream_and_respond())

ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown of the bot and graph."""
    global agent_executor
    
    # Connect to the SQLite database
    conn = await aiosqlite.connect("database.db")
    
    # Initialize the checkpointer with the connection
    memory = AsyncSqliteSaver(conn=conn)
    
    # Compile the graph with the checkpointer
    agent_executor = workflow.compile(checkpointer=memory)
    
    # Set up the Telegram webhook
    webhook_endpoint = f"{WEBHOOK_URL}/telegram"
    await ptb_app.bot.set_webhook(url=webhook_endpoint)
    logger.info(f"Webhook set to {webhook_endpoint}")
    
    async with ptb_app:
        await ptb_app.start()
        logger.info("Lifespan start: Bot and graph are set up.")
        yield
        await ptb_app.stop()
        logger.info("Bot stopped.")

    # Close the database connection on shutdown
    await conn.close()
    logger.info("Database connection closed.")

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan)

@app.post("/telegram")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram updates by passing them to the bot."""
    try:
        req = await request.json()
        update = Update.de_json(req, ptb_app.bot)
        await ptb_app.process_update(update)
        return Response(status_code=HTTPStatus.OK)
    except Exception as e:
        logger.error(f"Error processing update: {e}", exc_info=True)
        return Response(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

@app.get("/healthcheck")
async def health_check():
    """Healthcheck endpoint to verify the service is running."""
    return {"status": "ok"} 