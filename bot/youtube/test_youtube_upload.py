# test_youtube_upload.py
import os
import logging
from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2Credentials

CRED_FILE = "auth_token.txt"  # Ensure this is your saved auth file
logging.basicConfig(level=logging.INFO)

def test_youtube_auth():
    if not os.path.exists(CRED_FILE):
        print(f"❌ Credential file '{CRED_FILE}' not found! Run /login and /save_auth_data first.")
        return

    storage = Storage(CRED_FILE)
    creds: OAuth2Credentials = storage.get()

    if not creds or creds.invalid:
        print("❌ Credentials invalid or expired! Re-authorize using /login.")
        return

    try:
        youtube = build("youtube", "v3", credentials=creds)
        # Simple test: list your own channels to check permissions
        response = youtube.channels().list(mine=True, part="id").execute()
        if "items" in response and len(response["items"]) > 0:
            print("✅ OAuth token works! YouTube API accessible. Upload scope should work too.")
        else:
            print("⚠️ Token works but no channels found. Still, upload scope should work.")
    except Exception as e:
        print(f"❌ Error accessing YouTube API: {e}")

if __name__ == "__main__":
    test_youtube_auth()
