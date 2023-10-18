import hashlib
import hmac
from werkzeug.wrappers import Request
from werkzeug.exceptions import Unauthorized


class ClickupAuthenticator:
    signatureKey = "X-Signature"

    def __init__(self, secret: str):
        self.secret = secret

    def authenticate(self, request: Request):
        calculated_hmac = hmac.new(
            bytes(self.secret, "utf-8"),
            msg=request.data,
            digestmod=hashlib.sha256,
        ).hexdigest()

        if self.signatureKey not in request.headers:
            raise Unauthorized("Missing X-Signature header")

        if request.headers[self.signatureKey] != calculated_hmac:
            raise Unauthorized("Incorrect HMAC")
