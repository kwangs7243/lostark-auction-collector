from src.lostark_api import search_market_item
from src.price_parser import extract_price_data
import src.abidos_calculator as ac


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
result = ac.build_calculation_prices(lumber_prices)

required_materials = ac.get_required_materials()
owned_materials = {
    "목재" : 3333,
    "부드러운목재" : 2222,
    "아비도스목재" : 1111
}
if not ac.can_craft(owned_materials,required_materials):
    missing_materials = ac.get_missing_materials(owned_materials,required_materials)
    
    


