import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

# We get the public key and format it properly in case it has literal '\n' or quotes encoded in .env
raw_key = os.getenv("SUPABASE_JWT_PUBLIC_KEY", "").strip('"').replace("\\n", "\n")

if raw_key:
    if not raw_key.startswith("-----BEGIN PUBLIC KEY-----"):
        raw_key = "-----BEGIN PUBLIC KEY-----\n" + raw_key
    if not raw_key.endswith("-----END PUBLIC KEY-----"):
        raw_key = raw_key + "\n-----END PUBLIC KEY-----"

SUPABASE_JWT_PUBLIC_KEY = raw_key

security = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Validates the Supabase JWT token and extracts the user_id (sub claim).
    The algorithm MUST be RS256 using the Supabase JWT Public Key.
    """
    if not SUPABASE_JWT_PUBLIC_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_JWT_PUBLIC_KEY environment variable is not set or properly configured"
        )

    token = credentials.credentials

    try:
        # Validate the token using the public key and RS256 algorithm
        # We disable verification of 'aud' by default because Supabase might return custom audiences,
        # but the cryptographic signature and expiration are still fully validated.
        payload = jwt.decode(
            token,
            SUPABASE_JWT_PUBLIC_KEY,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )

        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload is missing the 'sub' claim (user_id)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_id

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
