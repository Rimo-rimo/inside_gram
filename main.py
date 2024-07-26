import os
from fastapi import FastAPI, Depends, HTTPException, Header, status, Security
from fastapi.security.api_key import APIKeyHeader, APIKey
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from supabase import create_client, Client
from sqlalchemy.orm import Session
from typing_extensions import Annotated
from datetime import date
import requests
from auth import get_current_user
import ast

from utils.clova_studio import get_reaction, get_emotion, get_embedding
from utils.milvus import get_memory

import dotenv
dotenv.load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

app = FastAPI()

emotion_dict = {"기쁨":1, "슬픔":2, "분노":3, "불안":4}
emotino_name = {1:"joy", 2:"sadness", 3:"anger", 4:"anxiety"}

class DiaryCreate(BaseModel):
    content: str

@app.get("/test/get_token")
def get_user_info():
    response = supabase.auth.sign_in_with_password({"email": "string@naver.com", "password": "string"})
    return response.session.access_token

@app.get("/diary")
def get_diary(user_id = Depends(get_current_user)):
    response = (supabase.table("diary").select("*").eq("user_id", user_id).execute())
    return response.data

@app.post("/diary")
def create_diary(data: DiaryCreate, user_id = Depends(get_current_user)):
    diary_data = {"user_id": user_id, "content": data.content}

    # 일기 DB 저장
    diary_db_response = supabase.table("diary").insert({"user_id": diary_data["user_id"],"content": diary_data["content"]}).execute()

    # 감정 생성
    emotions = ast.literal_eval(get_emotion(data.content))
    emotions_num = [emotion_dict[i] for i in emotions]
    
    emotion_reaction_list = []
    for emotion in emotions_num:
        # 일기-감정 DB 저장
        diary_emotion_db_response = supabase.table("diary_emotion").insert({"diary_id": diary_db_response.data[0]["diary_id"], "emotion_id": emotion}).execute()
        # 감정 반응 생성
        emotion_reaction = get_reaction(emotino_name[emotion], data.content)
        emotion_reaction_list.append(emotion_reaction)
        # 감정 반응 저장
        emotion_reaction_db_response = supabase.table("emotion_reaction").insert({"diary_emotion_id": diary_emotion_db_response.data[0]["diary_emotion_id"], "reaction": emotion_reaction}).execute()
        
    result = {"user_id":user_id, "diary_id":diary_db_response.data[0]["diary_id"], "reaction":[]}

    for emotion_i, emotion_reaction_i in zip(emotions_num, emotion_reaction_list):
        result["reaction"].append({"emotion_type": emotino_name[emotion_i], "content":emotion_reaction_i})

    return result

@app.post("/memory")
def search_memory(content: str, user_id = Depends(get_current_user)):
    memories = get_memory(content)
    return memories[0][0]["entity"]["text"]


@app.get("/diary/{diary_id}")
def read_diary(diary_id: int,  user_id = Depends(get_current_user)):
    diary_data = supabase.table("diary").select("*").eq("user_id", user_id).eq("diary_id", diary_id).execute()
    if diary_data.data:
        result = {"user_id":user_id, "diary_id": diary_data.data[0]["content"], "reaction":[]}
        diary_emotion_data = (supabase.table("diary_emotion").select("*").eq("diary_id", diary_id).execute())
        for i in diary_emotion_data.data:
            diary_emotion_id = i["diary_emotion_id"]
            emotion_reaction_data = (supabase.table("emotion_reaction").select("*").eq("diary_emotion_id", diary_emotion_id).execute())
            if i["emotion_id"] == 1:
                re = {"emotion_type": "joy", "content":emotion_reaction_data.data[0]["reaction"]}
            else:
                re = {"emotion_type": "sadness", "content":emotion_reaction_data.data[0]["reaction"]}
            result["reaction"].append(re)
        return result
    else:
        return diary_data.data
