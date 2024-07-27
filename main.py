import os
from fastapi import FastAPI, Depends, HTTPException, Header, status, Security
from fastapi.security.api_key import APIKeyHeader, APIKey
from pydantic import BaseModel, Field
from typing import Optional, List
import uvicorn
from supabase import create_client, Client
from sqlalchemy.orm import Session
from typing_extensions import Annotated
from datetime import date
from datetime import datetime
import requests
from auth import get_current_user
import ast
from typing import List, Dict
from utils.clova_studio import get_reaction, get_emotion, get_embedding
from utils.milvus import get_memory
from collections import Counter

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

class EmotionReaction(BaseModel):
    emotion_type: str
    content: str

class DiaryList(BaseModel):
    diary_id: int

# class DiaryListResponse(BaseModel):
#     diary_id : int
#     user_id : str
#     main_emotion: str
#     created_at

class DiaryItem(BaseModel):
    diary_id: int
    user_id: str
    content: str
    created_at: datetime
    memory_content: str
    main_emotion: str

class MainEmotionResponse(BaseModel):
    main_emotion:str

class MemoryContent(BaseModel):
    memory_content:str

# class DiaryListItem(BaseModel):
#     diary_id: int
#     content: str
#     created_at: datetime
#     memory_content: str
#     main_emotion: str

class DiaryListRquest(BaseModel):
    data : List[DiaryItem]

a = [{'emotion_type':'joy', 'content': "우와 대박이당!"},{'emotion_type':'sadness', 'content': "우와 슬프당!"}]

class DiaryResponse(BaseModel):
    user_id: str = Field(..., description="유저 고유 번호",example="12sdf-234...12sdf")
    diary_id: int = Field(..., description="일기 고유 번호",example="1")
    content: str = Field(..., description="작성한 일기",example="집중하자 집중해! 이것은 일기다")
    reaction: List[EmotionReaction] = Field(..., description="감정이들의 반응",example=a)
    main_emotion: str = Field(..., description="메인 감정",example="joy")
    memory_content: str = Field(..., example="오늘은 엄청 집중이 잘 되는 날이다.")

@app.get("/test/get_token")
def get_user_info():
    response = supabase.auth.sign_in_with_password({"email": "string@naver.com", "password": "string"})
    return response.session.access_token

# 다이어리 리스트
@app.get("/diary") 
def get_diary(user_id = Depends(get_current_user)):
    response = (supabase.table("diary").select("*").eq("user_id", user_id).execute())
    # result = []
    # for i in response.data:
    #     result.append(i["diary_id"])
    
    # result = response.data
    # for i in result:
    #     diary_data = supabase.table("diary").select("*").eq("user_id", user_id).eq("diary_id", i["diary_id"]).execute()
    #     i["main_emotion"] = diary_data
    # result["main_emotion"]
    return response.data

@app.get("/main_emotion")
def get_main_emotion(user_id = Depends(get_current_user)) -> MainEmotionResponse:
    response = (supabase.table("diary").select("*").eq("user_id", user_id).execute()).data[:15]
    # emotion_list = Counter([i["main_emotion"] for i in response])
    # emotion_list = dict(sorted(emotion_list.items(), key=lambda item: item[1]))
    if len(response) <= 0:
        return {"main_emotion":"joy"}
    else:
        emotion_list = Counter([i["main_emotion"] for i in response])
        emotion_list = dict(sorted(emotion_list.items(), key=lambda item: item[1], reverse=True))
        main_emotion = list(emotion_list.keys())[0]
        return {"main_emotion":main_emotion}

@app.get("/memory")
def get_memory_content(user_id = Depends(get_current_user)) -> MemoryContent:
    response = (supabase.table("diary").select("*").eq("user_id", user_id).execute()).data[:2]
    # emotion_list = Counter([i["main_emotion"] for i in response])
    # emotion_list = dict(sorted(emotion_list.items(), key=lambda item: item[1]))
    if len(response) <= 0:
        return "아직 일기가 없습니다."
    else:
        return {"memory_content":response[0]["memory_content"]}
        
# 다이어리 생성
@app.post("/diary")
def create_diary(data: DiaryCreate, user_id = Depends(get_current_user)) -> DiaryResponse:
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
        
    result = {"user_id":user_id, "diary_id":diary_db_response.data[0]["diary_id"], "content":data.content, "main_emotion":emotino_name[emotions_num[0]], "reaction":[]}

    response = (
        supabase.table("diary")
        .update({"main_emotion": emotino_name[emotions_num[0]]})
        .eq("diary_id", diary_db_response.data[0]["diary_id"])
        .execute()
    )
    for emotion_i, emotion_reaction_i in zip(emotions_num, emotion_reaction_list):
        result["reaction"].append({"emotion_type": emotino_name[emotion_i], "content":emotion_reaction_i})
    
    memory_content = search_memory(data.content, user_id)

    response = (
        supabase.table("diary")
        .update({"memory_content": memory_content})
        .eq("diary_id", diary_db_response.data[0]["diary_id"])
        .execute()
    )

    result["memory_content"] = memory_content
    return result

# @app.post("/memory")
def search_memory(content: str, user_id = Depends(get_current_user)):
    memories = get_memory(content, user_id)
    return memories[0][0]["entity"]["text"]

# @app.get("/test/test")
# def test():
#     user_id = "2b2b145c-5cdd-4fa7-9638-e0202f994147"
#     response = (supabase.table("diary").select("*").eq("user_id", user_id).execute())
#     diary_id_list = []
#     for i in response.data:
#         # diary_id_list.append(i["diary_id"])
#         memory_content = search_memory(i["content"], user_id)
#         response = (
#             supabase.table("diary")
#             .update({"memory_content": memory_content})
#             .eq("diary_id", i["diary_id"])
#             .execute()
#         )
#         print(response)

    # rr = []
    # try:
    #     for i in diary_id_list:
    #         diary_emotion_data = (supabase.table("diary_emotion").select("*").eq("diary_id", i).execute())
    #         diary_emotion_id = diary_emotion_data.data[0]["emotion_id"]
    #         print(diary_emotion_id)
    #         # print(diary_emotion_id)
    #         # emotion_reaction_data = (supabase.table("emotion_reaction").select("*").eq("diary_emotion_id", diary_emotion_id).execute())
    #         # rr.append(emotion_reaction_data)
    #         # response = (
    #         #     supabase.table("diary")
    #         #     .update({"main_emotion": emotino_name[diary_emotion_id]})
    #         #     .eq("diary_id", i)
    #         #     .execute()
    #         # )
    # except:
    #     pass
    # return "ss"

"""
class DiaryResponse(BaseModel):
    user_id: str = Field(..., description="유저 고유 번호",example="12sdf-234...12sdf")
    diary_id: int = Field(..., description="일기 고유 번호",example="1")
    content: str = Field(..., description="작성한 일기",example="집중하자 집중해! 이것은 일기다")
    reaction: List[EmotionReaction] = Field(..., description="감정이들의 반응",example=a)
    main_emotion: str = Field(..., description="메인 감정",example="joy")
    memory_content: str = Field(..., example="오늘은 엄청 집중이 잘 되는 날이다.")
"""


# 다이어리 세부 조회
@app.get("/diary/{diary_id}")
def read_diary(diary_id: int,  user_id = Depends(get_current_user)) -> DiaryResponse:
    diary_data = supabase.table("diary").select("*").eq("user_id", user_id).eq("diary_id", diary_id).execute()
    # if diary_data.data:
    result = {"user_id":user_id, "diary_id": diary_data.data[0]["diary_id"], "reaction":[], "content": diary_data.data[0]["content"], "main_emotion":diary_data.data[0]["main_emotion"], "memory_content":diary_data.data[0]["memory_content"]}
    diary_emotion_data = (supabase.table("diary_emotion").select("*").eq("diary_id", diary_id).execute())
    for i in diary_emotion_data.data:
        diary_emotion_id = i["diary_emotion_id"]
        emotion_reaction_data = (supabase.table("emotion_reaction").select("*").eq("diary_emotion_id", diary_emotion_id).execute())
        re = {"emotion_type": emotino_name[i["emotion_id"]], "content":emotion_reaction_data.data[0]["reaction"]}
        result["reaction"].append(re)
    return result
    # else:
    #     return diary_data.data
