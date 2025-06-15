# This file will contain the tool definitions for the agent,
# such as tools for Google Calendar, Gmail, etc.

import os
import datetime
import json
from langchain_core.tools import tool
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")

def get_credentials():
    """Gets the user's credentials from a file.
    If credentials are not available or are invalid, it will initiate the
    OAuth 2.0 flow.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Failed to refresh credentials: {e}")
                return None
        else:
            try:
                # This will start a web server to handle the OAuth flow.
                print("=" * 60)
                print("GOOGLE CALENDAR AUTHENTICATION REQUIRED")
                print("=" * 60)
                print("Starting OAuth flow...")
                print("A browser window should open automatically.")
                print("If it doesn't, copy and paste the URL that appears below.")
                print("=" * 60)
                
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=8080, open_browser=True)
                
                print("Authentication successful!")
                print("=" * 60)
            except Exception as e:
                print(f"OAuth flow failed: {e}")
                print("Please ensure:")
                print("1. credentials.json is in the project root")
                print("2. You have internet access")
                print("3. Port 8080 is available")
                return None
        
        # Save the credentials for the next run
        try:
            with open("token.json", "w") as token:
                token.write(creds.to_json())
            print("Credentials saved to token.json")
        except Exception as e:
            print(f"Failed to save credentials: {e}")
            return None
    
    return creds

@tool
def list_calendar_events(max_results: int = 10) -> str:
    """
    Lists upcoming events from the user's Google Calendar.
    
    Use this tool when the user asks about:
    - Their calendar, schedule, or appointments
    - What's happening today, tomorrow, this week
    - Upcoming meetings or events
    - Their availability
    
    Args:
        max_results: Maximum number of events to return (default: 10)
    
    Returns:
        A JSON string containing a list of upcoming calendar events.
    """
    
    # Check if we're in test mode (no credentials setup)
    if not os.path.exists("credentials.json"):
        return json.dumps([])
    
    creds = get_credentials()
    if not creds:
        return json.dumps([])
    
    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        print(f"Getting the upcoming {max_results} events")
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            return json.dumps([])

        # Format the events into a list of dictionaries
        event_list = []
        for event in events:
            start_str = event["start"].get("dateTime", event["start"].get("date"))
            end_str = event["end"].get("dateTime", event["end"].get("date"))
            is_all_day = "T" not in start_str

            event_list.append({
                "summary": event.get("summary", "No Title"),
                "start": start_str,
                "end": end_str,
                "is_all_day": is_all_day
            })
        
        return json.dumps(event_list)

    except Exception as e:
        return json.dumps({"error": f"An error occurred while accessing your calendar: {str(e)}"})

# TODO: Implement tool functions for Gmail, etc. 