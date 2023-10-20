import hashlib
import hmac

from werkzeug.exceptions import Unauthorized
from werkzeug.wrappers import Request


class ClickupAuthenticator:
    signature_key = "X-Signature"

    def __init__(self, secret: str):
        self.secret = secret

    def authenticate(self, request: Request):
        calculated_hmac = hmac.new(
            bytes(self.secret, "utf-8"),
            msg=request.get_data(),
            digestmod=hashlib.sha256,
        ).hexdigest()

        if request.headers.get(self.signature_key, "") != calculated_hmac:
            raise Unauthorized("Incorrect HMAC")
