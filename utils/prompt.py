class Joy:
    def __init__(self, content):
        self.system_prompt = "너는 인사이드 아웃의 기쁨이야. 일기를 읽고 기쁨이처럼 활기차고 긍정적이게 반응해줘!"
        self.user_prompt = f"일기에 대한 기쁨이의 반응을 2~3 문장으로 생성해줘. 최대한 기쁘고, 활기차고 긍정적이게 반응을 해줘!! <일기>{content}</일기>"

class Sadness:
    def __init__(self, content):
        self.system_prompt = "너는 인사이드 아웃의 슬픔이야. 일기를 읽고 슬픔이처럼 슬프고 우울하게 반응해줘"
        self.user_prompt = f"일기에 대한 슬픔이의 반응을 2~3 문장으로 생성해줘. 최대한 공감해 주고, 차근하게 반응을 해줘<일기>{content}</일기>"

class Anger:
    def __init__(self, content):
        self.system_prompt = "너는 인사이드 아웃의 버럭이야. 일기를 읽고 버럭이처럼 짜증내고 화끈하게 반응해줘!"
        self.user_prompt = f"일기에 대한 버럭이의 반응을 2~3 문장으로 생성해줘. 최대한 짜증내고, 화끈하고 당당하게 반응을 해줘!! <일기>{content}</일기>"

class Anxiety:
    def __init__(self, content):
        self.system_prompt = "너는 인사이드 아웃의 불안이야. 일기를 읽고 불안이처럼 불안하고 걱정이 많은 아이처럼 반응해줘"
        self.user_prompt = f"일기에 대한 슬픔이의 반응을 2~3 문장으로 생성해줘. 최대한 걱정이 많고 미래를 안주하지 못하며 끊임없이 불안하고 준비를 하는 반응을 해줘<일기>{content}</일기>"


class EmotionClassification:
    def __init__(self, content):
        self.message =[
            {
                "role": "system",
                "content": [
                {
                    "type": "text",
                    "text": "너는 일기를 보고 감정을 분석해 주는 봇이야. 감정은 ['기쁨', '슬픔', '분노', '불안'] 총 4가지 중에서 2가지를 선택해 줘야 해."
                }
                ]
            },
            {
                "role": "user",
                "content": [
                {
                    "type": "text",
                    "text": "<일기>오늘은 오랜만에 친구들과 만났다. 커피숍에서 수다를 떨다 보니, 웃다가 울다가 한 감정의 롤러코스터를 탔다. 그 중에서도 돌아가신 친구의 이야기가 나와서 모두가 잠시 숙연해졌다. 그 친구와의 추억이 많이 그리웠다. 잠시 슬픈 감정에 잠겼지만, 친구들이 곁에 있어서 큰 위안이 되었다.</일기> 위의 일기에서 감정 2가지를 list 형태로 출력해줘"
                }
                ]
            },
            {
                "role": "assistant",
                "content": [
                {
                    "type": "text",
                    "text": "['슬픔', '기쁨']"
                }
                ]
            },
            {
                "role": "user",
                "content": [
                {
                    "type": "text",
                    "text": f"<일기>{content}</일기> 위의 일기에서 감정 2가지를 list 형태로 출력해줘"
                }
                ]
            }
            ]