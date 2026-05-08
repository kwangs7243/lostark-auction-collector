from src.lostark_api import search_market_item
from src.price_parser import extract_price_data
from src.abidos_calculator import build_calculation_prices, get_required_materials, can_craft


CATEGORY_CODES = {
    "재련재료": 50010,
    "벌목전리품": 90300,
}


def get_lumber_prices() -> dict:
    result = search_market_item(category_code=CATEGORY_CODES["벌목전리품"])
    return extract_price_data(result)


def get_abidos_price() -> dict:
    result = search_market_item(item_name="상급 아비도스", category_code=CATEGORY_CODES["재련재료"])
    return extract_price_data(result)


lumber_prices = get_lumber_prices()
abidos_price = get_abidos_price()
result = build_calculation_prices(lumber_prices)

required_materials = get_required_materials()
owned_materials = {
    "목재" : 99999,
    "부드러운목재" : 9999,
    "아비도스목재" : 99999
}
print(can_craft(owned_materials,required_materials))


