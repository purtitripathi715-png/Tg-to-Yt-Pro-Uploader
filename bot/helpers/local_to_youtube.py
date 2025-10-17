import os
import asyncio
import logging
from googleapiclient.http import MediaFileUpload
from helpers.auth import GoogleAuth  # aapka GoogleAuth class
from config import Config

# ------------------ Logging ------------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("LocalUploader")

# ------------------ Folders ------------------
DOWNLOAD_FOLDER = "downloads"
UPLOADED_FOLDER = "uploaded"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(UPLOADED_FOLDER, exist_ok=True)

# ------------------ Google Authentication ------------------
auth = GoogleAuth(Config.CLIENT_ID, Config.CLIENT_SECRET)
auth.LoadCredentialsFile(Config.CRED_FILE)
yt = auth.authorize()


# ------------------ Upload Function ------------------
async def upload_file(file_path: str, title: str):
    loop = asyncio.get_event_loop()

    def blocking_upload():
        try:
            media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
            request = yt.videos().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": "Uploaded via VIP YOUTUBE UPLOADER Bot",
                        "tags": ["VIP YouTube Uploader"],
                    },
                    "status": {"privacyStatus": "private"},
                },
                media_body=media,
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    log.info(f"Upload progress: {int(status.progress() * 100)}%")

            video_id = response.get("id")
            video_url = f"https://youtu.be/{video_id}"
            log.info(f"✅ Uploaded: {video_url}")
            return True, video_url

        except Exception as e:
            log.error(f"❌ Upload failed: {e}", exc_info=True)
            return False, str(e)

    return await loop.run_in_executor(None, blocking_upload)


# ------------------ Main Function ------------------
async def main():
    files = [
        f for f in os.listdir(DOWNLOAD_FOLDER)
        if os.path.isfile(os.path.join(DOWNLOAD_FOLDER, f))
    ]

    if not files:
        log.info("No videos found in local folder.")
        return

    for file_name in files:
        file_path = os.path.join(DOWNLOAD_FOLDER, file_name)
        title = os.path.splitext(file_name)[0]  # file name as title
        success, result = await upload_file(file_path, title)
        if success:
            # Move uploaded file
            os.rename(file_path, os.path.join(UPLOADED_FOLDER, file_name))
        else:
            log.warning(f"Failed to upload {file_name}: {result}")


# ------------------ Entry Point ------------------
if __name__ == "__main__":
    asyncio.run(main())
