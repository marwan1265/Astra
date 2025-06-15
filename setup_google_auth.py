#!/usr/bin/env python3
"""
Google Calendar Authentication Setup Script

This script helps you set up Google Calendar authentication for your secretary agent.
Run this script to generate the token.json file needed for calendar access.
"""

import os
import sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDENTIALS_FILE = "credentials.json"

def setup_google_auth():
    """Set up Google Calendar authentication."""
    
    # Check if credentials.json exists
    if not os.path.exists(CREDENTIALS_FILE):
        print("❌ Error: credentials.json not found!")
        print("\nTo get credentials.json:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable the Google Calendar API")
        print("4. Go to 'Credentials' → 'Create Credentials' → 'OAuth client ID'")
        print("5. Choose 'Desktop application'")
        print("6. Download the JSON file and rename it to 'credentials.json'")
        print("7. Place it in this directory")
        return False
    
    print("✅ Found credentials.json")
    
    # Check if token.json already exists
    if os.path.exists("token.json"):
        print("✅ token.json already exists")
        
        # Try to load and validate existing credentials
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            if creds and creds.valid:
                print("✅ Existing credentials are valid!")
                return True
            elif creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired credentials...")
                creds.refresh(Request())
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
                print("✅ Credentials refreshed successfully!")
                return True
        except Exception as e:
            print(f"⚠️  Existing token.json is invalid: {e}")
            print("🔄 Creating new token...")
    
    # Start OAuth flow
    try:
        print("\n" + "="*60)
        print("🚀 STARTING GOOGLE CALENDAR AUTHENTICATION")
        print("="*60)
        print("📝 Instructions:")
        print("1. A browser window will open automatically")
        print("2. Sign in to your Google account")
        print("3. Grant permission to access your calendar")
        print("4. The browser will show a success message")
        print("5. Return to this terminal")
        print("="*60)
        
        input("Press Enter to continue...")
        
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=8080, open_browser=True)
        
        # Save the credentials for future use
        with open("token.json", "w") as token:
            token.write(creds.to_json())
        
        print("\n" + "="*60)
        print("🎉 SUCCESS! Google Calendar authentication complete!")
        print("✅ token.json has been created")
        print("✅ Your secretary agent can now access your calendar")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        print("\nTroubleshooting:")
        print("• Make sure port 8080 is not in use")
        print("• Check your internet connection")
        print("• Verify credentials.json is valid")
        print("• Try running the script again")
        return False

if __name__ == "__main__":
    print("🤖 Secretary Agent - Google Calendar Setup")
    print("="*50)
    
    success = setup_google_auth()
    
    if success:
        print("\n🚀 Next steps:")
        print("1. Start your secretary agent: python main.py")
        print("2. Ask your Telegram bot: 'What's on my calendar today?'")
        print("3. Enjoy your personal secretary! 🎉")
    else:
        print("\n❌ Setup failed. Please check the errors above and try again.")
        sys.exit(1) 