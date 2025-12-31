from jose import jwt, JWTError

SECRET_KEY = "dev-secret-key-change-later"
ALGORITHM = "HS256"


def verify_and_decode_jwt(token: str) -> dict:
    """
    Verify JWT signature and return decoded claims.
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False},  # Disable expiration verification for dev. Change later.
        )
        return payload
    except JWTError:
        raise ValueError("Invalid or expired JWT")

