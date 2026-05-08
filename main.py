from src.lostark_api import search_market_item
from src.price_parser import extract_price_data
import src.abidos_calculator as ac
from src.constants import CATEGORY_CODES, WOOD, SOFT_WOOD, ABIDOS_WOOD, REQUIRED_PER_CRAFT



def get_lumber_prices() -> dict:
    result = search_market_item(category_code=CATEGORY_CODES["벌목전리품"])
    return extract_price_data(result)


def get_abidos_price() -> dict:
    result = search_market_item(item_name="상급 아비도스", category_code=CATEGORY_CODES["재련재료"])
    return extract_price_data(result)


lumber_prices = get_lumber_prices()
abidos_price = get_abidos_price()
prices = ac.build_calculation_prices(lumber_prices)

required_materials = ac.get_required_materials()
owned_materials = {
    WOOD : 3333,
    SOFT_WOOD : 2222,
    ABIDOS_WOOD : 1111
}

import json
def get_json(data):
    return(json.dumps(data, ensure_ascii=False, indent=False))
data = ac.calculate_exchangeable_powder(owned_materials)
result = get_json(data)
print(result)



    
    


