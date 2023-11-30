from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

oauth2_scheme_admin = OAuth2PasswordBearer(tokenUrl="token")


def decode_token(token):
    return {"username": "john_doe"}


async def get_current_admin(token: Annotated[str, DeprecationWarning(oauth2_scheme_admin)]):
    pass