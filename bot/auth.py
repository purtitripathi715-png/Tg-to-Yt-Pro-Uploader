from typing import Optional
import httplib2
import os

from apiclient import discovery
from oauth2client.client import (
    OAuth2WebServerFlow,
    FlowExchangeError,
    OAuth2Credentials,
)
from oauth2client.file import Storage
from flask import Flask, request

class AuthCodeInvalidError(Exception):
    pass


class InvalidCredentials(Exception):
    pass


class NoCredentialFile(Exception):
    pass


class GoogleAuth:
    OAUTH_SCOPE = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube"
    ]
    REDIRECT_URI = "http://localhost:8080/callback"
    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"

    def __init__(self, CLIENT_ID: str, CLIENT_SECRET: str):
        self.flow = OAuth2WebServerFlow(
            CLIENT_ID, CLIENT_SECRET, self.OAUTH_SCOPE, redirect_uri=self.REDIRECT_URI
        )
        self.credentials: Optional[OAuth2Credentials] = None

    def GetAuthUrl(self) -> str:
        return self.flow.step1_get_authorize_url()

    def Auth(self, code: str) -> None:
        try:
            self.credentials = self.flow.step2_exchange(code)
        except FlowExchangeError as e:
            raise AuthCodeInvalidError(e)
        except Exception:
            raise

    def authorize(self):
        try:
            if self.credentials:
                http = httplib2.Http()
                self.credentials.refresh(http)
                http = self.credentials.authorize(http)
                return discovery.build(
                    self.API_SERVICE_NAME, self.API_VERSION, http=http
                )
            else:
                raise InvalidCredentials("No credentials!")
        except Exception:
            raise

    def LoadCredentialsFile(self, cred_file: str) -> None:
        if not os.path.isfile(cred_file):
            raise NoCredentialFile(
                f"No credential file named {cred_file} is found."
            )
        storage = Storage(cred_file)
        self.credentials = storage.get()

    def SaveCredentialsFile(self, cred_file: str) -> None:
        storage = Storage(cred_file)
        storage.put(self.credentials)


# --------------------- Flask Integration ---------------------

app = Flask(__name__)
CLIENT_ID = "1096672036757-49rn9etongdtji64p793mfp0vigoup8i.apps.googleusercontent.com"
CLIENT_SECRET = "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"
CRED_FILE = "credentials.json"  # File jisme auth save hoga
auth = GoogleAuth(CLIENT_ID, CLIENT_SECRET)

@app.route('/')
def index():
    auth_url = auth.GetAuthUrl()
    return f'<a href="{auth_url}">Click here to authorize YouTube</a>'

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "No code received!"
    try:
        auth.Auth(code)
        # ✅ Save credentials automatically
        auth.SaveCredentialsFile(CRED_FILE)
        return f"Auth code received and credentials saved in {CRED_FILE}!"
    except AuthCodeInvalidError as e:
        return f"Invalid auth code: {e}"
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    app.run(port=8080, debug=True)
