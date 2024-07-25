from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader, APIKey
from supabase import create_client, Client
import os
import dotenv
dotenv.load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# 토큰으로 부터 유저 정보 추출
def get_current_user(api_key: str = Security(api_key_header)):
    if api_key is None:
        raise HTTPException(status_code=403, detail="Not authenticated")
    token = api_key.split(" ")[1] if " " in api_key else api_key
    response = supabase.auth.get_user(token)
    return response.user.id