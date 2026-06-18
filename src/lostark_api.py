import os

import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("api_key")
url = "https://developer-lostark.game.onstove.com/markets/items"

headers = {
    "Authorization": f"bearer {api_key}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def search_market_item(
    item_name: str = "",
    category_code: int = None,
    character_class: str = "",
    item_tier: int | None = None,
    item_grade: str = "",
    page_no: int = 1,
) -> dict:
    """로스트아크 거래소 검색 API를 호출하고 응답 JSON을 반환한다."""
    if not api_key:
        raise ValueError("로스트아크 API 키가 없습니다.")

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

    response = requests.post(
        url,
        headers=headers,
        json=body,
    )
    response.raise_for_status()

    return response.json()
