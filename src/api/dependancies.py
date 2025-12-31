from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.auth.jwt import verify_and_decode_jwt
from src.security.user_context import UserContext

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserContext:
    """
    Extract and validate JWT from Authorization header
    and return authenticated UserContext.
    """
    try:
        claims = verify_and_decode_jwt(credentials.credentials)
        user = UserContext(
            user_id=claims["sub"],
            department=claims.get("department", ""),
            clearance=claims.get("clearance", 0),
            projects=claims.get("projects", []),
            raw_token=credentials.credentials
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    

    return user
