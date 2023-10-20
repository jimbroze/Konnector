import base64
import hashlib
import hmac

from werkzeug.exceptions import Unauthorized
from werkzeug.wrappers import Request


class TodoistAuthenticator:
    signature_key = "X-Todoist-Hmac-SHA256"
    user_agent = "Todoist-Webhooks"

    def __init__(self, secret: str):
        self.secret = secret

    def authenticate(self, request: Request):
        if request.headers.get("User-Agent", "") != self.user_agent:
            raise Unauthorized("Bad user agent")

        calculated_hmac = base64.b64encode(
            hmac.new(
                bytes(self.secret, "utf-8"),
                msg=request.get_data(),
                digestmod=hashlib.sha256,
            ).digest()
        ).decode("utf-8")

        if request.headers.get(self.signature_key, "") != calculated_hmac:
            raise Unauthorized("Incorrect HMAC")
