import os
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from datetime import datetime, timedelta

API_KEY_NAME = "X-API-Key"
API_KEY_HEADER = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Store API keys with their expiration dates
api_keys = {}

def load_api_keys():
    # Load API keys from environment variables
    api_key = os.getenv("API_KEY")
    if api_key:
        # Set expiration to 30 days from now
        api_keys[api_key] = datetime.now() + timedelta(days=30)

load_api_keys()

async def validate_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key not in api_keys:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate API key"
        )
    
    # Check if the API key has expired
    if datetime.now() > api_keys[api_key]:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="API key has expired"
        )
    
    return api_key