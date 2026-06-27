from src.constants import CATEGORY_CODES
from src.lostark_api import search_market_item
from src.price_parser import extract_price_data


def get_lumber_prices() -> dict:
    """거래소 API에서 벌목 전리품 가격 정보를 가져온다."""
    result = search_market_item(
        category_code=CATEGORY_CODES["벌목전리품"],
    )
    return extract_price_data(result)


def get_market_prices() -> dict:
    """계산에 필요한 시장 가격 정보를 하나의 dict로 합친다."""
    return get_lumber_prices()
