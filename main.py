from src.lostark_api import search_market_item
from src.price_parser import extract_price_data
import src.abidos_calculator as ac
from src.constants import CATEGORY_CODES, WOOD, SOFT_WOOD, ABIDOS_WOOD, POWDER



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
    WOOD : 13333,
    SOFT_WOOD : 2222,
    ABIDOS_WOOD : 1111
}
missing_materials = ac.get_missing_materials(owned_materials,required_materials)
dic = ac.calculate_required_powder_for_abidos_wood(missing_materials)
required_powder = dic["필요한가루"]
remaining_materials = ac.calculate_remaining_materials(
    owned_materials,
    required_materials)
import json
def get_json(data):
    return(json.dumps(data, ensure_ascii=False, indent=4))
data =[ ac.calculate_powder_exchange_plan_by_material(owned_materials,required_powder)]

result = get_json(data)
print(result)



    
    


