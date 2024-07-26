import requests
import os
import dotenv
import json
from openai import OpenAI

from utils.prompt import Joy, Sadness, Anger, Anxiety, EmotionClassification

dotenv.load_dotenv()

client = OpenAI()

# 환경 변수 로드
CLOVASTUDIO_API_KEY = os.environ.get("X-NCP-CLOVASTUDIO-API-KEY")
APIGW_API_KEY = os.environ.get("X-NCP-APIGW-API-KEY")

reaction_headers = {
    'X-NCP-CLOVASTUDIO-API-KEY': CLOVASTUDIO_API_KEY,
    'X-NCP-APIGW-API-KEY': APIGW_API_KEY,
    'X-NCP-CLOVASTUDIO-REQUEST-ID': "8cb9d382-577e-4d5f-a3f8-85f9c016c32c",
    'Content-Type': 'application/json; charset=utf-8',
    }


embedding_headers = {
    'X-NCP-CLOVASTUDIO-API-KEY': CLOVASTUDIO_API_KEY,
    'X-NCP-APIGW-API-KEY': APIGW_API_KEY,
    'X-NCP-CLOVASTUDIO-REQUEST-ID': "4f5f51a0-acf0-484e-84c9-46cf2aa067f3",
    'Content-Type': 'application/json; charset=utf-8',
    }

emotion_type_dict = {"joy":Joy, "sadness":Sadness, "anger":Anger, "anxiety":Anxiety}

def get_emotion(content):

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages = EmotionClassification(content).message,
        temperature=1.0,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    return json.loads(response.json())["choices"][0]["message"]["content"]

def get_reaction(emotion_type, content):

    prompt = emotion_type_dict[emotion_type](content)

    request_data = {
        'messages': [{"role":"system","content":prompt.system_prompt},{"role":"user","content":prompt.user_prompt}],
        'topP': 0.8,
        'topK': 0,
        'maxTokens': 256,
        'temperature': 0.8,
        'repeatPenalty': 5.0,
        'stopBefore': [],
        'includeAiFilters': True,
        'seed': 0
        }

    reaction = requests.post("https://clovastudio.stream.ntruss.com" + '/testapp/v1/chat-completions/HCX-DASH-001', headers=reaction_headers, json=request_data).json()["result"]["message"]["content"]

    return reaction


def get_embedding(content):

    request_data = {
        "text": content
        }
    
    reaction = requests.post("https://clovastudio.apigw.ntruss.com/testapp/v1/api-tools/embedding/v2/4aacadacd0c048e98e14e4870c2f2c93", headers=embedding_headers, json=request_data).json()["result"]["embedding"]
    return reaction
