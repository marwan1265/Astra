# Secretary Agent

## Overview

The **Secretary Agent** is a personal assistant designed for a single user, accessible via **Telegram**. It's built with **LangGraph** and powered by **Google's Gemini 2.5 Pro** to understand and process your requests (though any LLM with agentic capabilites can be used in it's place with some modification). The agent can connect to your **Google Calendar** to help you manage your schedule, all through a simple and conversational interface.

This project is designed to be a stateful, single-user assistant that remembers your conversation history for a more natural interaction. It's an excellent foundation for building a more comprehensive personal AI secretary.

## Features

- **Telegram Interface**: Interact with the agent through natural language on Telegram.
- **Google Calendar Integration**:
  - Securely authenticates with your Google Account using OAuth 2.0.
  - Lists upcoming events from your primary calendar.
- **Intelligent Responses**: Uses Gemini 2.5 Pro to provide clear, well-formatted summaries of your schedule.
- **Stateful Conversations**: Remembers the context of your chat using a local SQLite database, allowing for more natural follow-up questions.
- **Secure**: Designed to respond only to a single, authorized Telegram user ID.

## Tech Stack

- **Language**: Python
- **Framework**: LangGraph (for stateful agent workflows)
- **LLM**: Google Gemini 2.5 Pro
- **Web Server**: FastAPI
- **Telegram Bot**: `python-telegram-bot`
- **Google Integration**: `google-api-python-client`
- **Database**: SQLite (for conversation memory)

## Setup and Installation Guide

Follow these steps to get your Secretary Agent up and running on your local machine.

### Step 1: Prerequisites

Before you begin, make sure you have the following installed:
- [Python 3.10+](https://www.python.org/downloads/)
- [ngrok](https://ngrok.com/download) to expose your local server to the internet for Telegram's webhook.

### Step 2: Clone the Repository

Clone this repository to your local machine:
```bash
git clone <repository-url>
cd secretary-agent
```

### Step 3: Install Dependencies

It's recommended to use a virtual environment to manage dependencies.
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

### Step 4: Set Up Google Credentials

The agent needs to authenticate with Google to access your calendar.

1.  **Enable the Google Calendar API**:
    - Go to the [Google Cloud Console](https://console.cloud.google.com/).
    - Create a new project or select an existing one.
    - In the navigation menu, go to **APIs & Services > Library**.
    - Search for "Google Calendar API" and enable it.

2.  **Create OAuth 2.0 Credentials**:
    - Go to **APIs & Services > Credentials**.
    - Click **Create Credentials > OAuth client ID**.
    - Select **Desktop app** as the application type.
    - After creation, click **DOWNLOAD JSON** for the client ID.
    - **Rename the downloaded file to `credentials.json`** and place it in the root directory of this project.

### Step 5: Configure Environment Variables

Create a file named `.env.local` in the project root. This file will store your secret keys and configuration. Copy and paste the following, filling in your own values.

```env
# .env.local

# 1. Google API Key for Gemini
# Get this from Google AI Studio: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"

# 2. Telegram Bot Token
# Get this by talking to @BotFather on Telegram
TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"

# 3. Your Personal Telegram Chat ID
# Get this by talking to @userinfobot on Telegram
YOUR_CHAT_ID="YOUR_TELEGRAM_CHAT_ID"

# 4. Webhook URL (from ngrok) - YOU WILL SET THIS IN A LATER STEP
WEBHOOK_URL=""
```
**Leave `WEBHOOK_URL` blank for now.**

### Step 6: Authorize Google Calendar Access

Run the provided script to authorize the agent to access your Google Calendar. This will use your `credentials.json` to launch a browser window where you can sign in and grant permission.

```bash
python setup_google_auth.py
```

After you complete the flow, a `token.json` file will be created in the project root. This file stores your authorization and will be used for all future calendar requests.

### Step 7: Start ngrok and Set the Webhook URL

Telegram sends updates to a public URL (a webhook). We'll use `ngrok` to create a secure tunnel to our local server.

1.  **Start ngrok**:
    Open a **new terminal window** and run the following command to expose port 8000:
    ```bash
    ngrok http 8000
    ```
2.  **Copy the URL**:
    `ngrok` will display a "Forwarding" URL that looks like `https://<random-string>.ngrok-free.app`. Copy the **HTTPS** URL.

3.  **Update Your Environment File**:
    - Go back to your `.env.local` file.
    - Paste the `ngrok` HTTPS URL as the value for `WEBHOOK_URL`.
    - **Save the file.**

### Step 8: Run the Agent!

Now you're ready to start the agent. In your original terminal (where you activated the virtual environment), run:

```bash
python main.py
```

If everything is set up correctly, you will see a message confirming that the webhook has been set. Your Secretary Agent is now live and will respond to your messages on Telegram!

## Usage

Once the agent is running, you can interact with it via your Telegram bot. Try asking:

- "What's on my calendar today?"
- "Do I have any meetings this week?"
- "What's my schedule like tomorrow?"

## Security

- **Access Control**: The agent is hard-coded to respond **only** to the `YOUR_CHAT_ID` you specified in your environment file. Messages from any other user will be ignored.
- **Credentials**: Your secret keys are stored locally in the `.env.local` file, which should not be committed to version control. The `.gitignore` file is already configured to ignore it.

## Contributing

Contributions are welcome! If you have ideas for new features or improvements, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
