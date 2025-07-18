import uuid
import jwt
from datetime import datetime, UTC


class AuthenticationUtils:
    
    @staticmethod
    def generate_token(client_secret: str, payload: dict) -> str:
      """
      Generate a JWT token using the client secret.
      """
      payload = {
          "iss": "PAYTM",
          "iat": int(datetime.now(UTC).timestamp())
      }
      
      token = jwt.encode(payload, client_secret, algorithm="HS256")
      # For pyjwt >= 2.0, token is returned as bytes, so decode to str
      if isinstance(token, bytes):
          token = token.decode("utf-8")
      return token
    
    
    @staticmethod
    def uuid_generator(merchant_id: str) -> str:
      """
      Generate a unique request message id by appending the merchant id to a UUID.
      """
      return f"{uuid.uuid4()}{merchant_id}"

