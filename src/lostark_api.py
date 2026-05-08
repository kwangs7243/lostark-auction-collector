from dotenv import load_dotenv
import os
import requests

load_dotenv()

api_key = os.environ.get('api_key')
url = "https://developer-lostark.game.onstove.com/markets/items"
headers = {
    "Authorization": f"bearer {api_key}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}
item_code ={
    "재련재료" : 50010,
    "벌목전리품" : 90300
}

def search_market_item(
    item_name: str = "",
    category_code: int = None,
    character_class: str = "",
    item_tier: int | None = None,
    item_grade: str = "",
    page_no: int = 1,
) -> dict:
    '''
    로스트아크 거래소 오픈 API에 요청을 보낸 결과를 반환한다
    '''
    body = {
        "Sort": "GRADE",
        "CategoryCode": category_code,
        "CharacterClass": character_class,
        "ItemTier": item_tier,
        "ItemGrade": item_grade,
        "ItemName": item_name,
        "PageNo": page_no,
        "SortCondition": "ASC",
    }

    response = requests.post(url, headers=headers, json=body)
    return response.json()