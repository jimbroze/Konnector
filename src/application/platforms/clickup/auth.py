import hashlib
import hmac
import requests

import application.exceptions as exceptions


class ClickupAuthenticator:
    signatureKey = "X-Signature"

    def __init__(self, secret: str):
        self.secret = secret

    def authenticate(self, request: requests.Request):
        calculated_hmac = hmac.new(
            bytes(self.secret, "utf-8"),
            msg=request.data,
            digestmod=hashlib.sha256,
        ).hexdigest()

        if request.headers[self.signatureKey] != calculated_hmac:
            raise exceptions.AuthenticationException("Incorrect HMAC")
