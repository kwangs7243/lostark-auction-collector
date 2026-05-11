import json

from src.lostark_api import search_market_item
from src.price_parser import extract_price_data
import src.abidos_calculator as ac
from src.constants import (
    CATEGORY_CODES,
    WOOD,
    SOFT_WOOD,
    ABIDOS_WOOD,
)


def get_lumber_prices() -> dict:
    result = search_market_item(
        category_code=CATEGORY_CODES["벌목전리품"]
    )
    return extract_price_data(result)


def get_abidos_price() -> dict:
    result = search_market_item(
        item_name="상급 아비도스",
        category_code=CATEGORY_CODES["재련재료"]
    )
    return extract_price_data(result)


def print_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=4))



craft_count = 40

owned_materials = {
    WOOD: 11000,
    SOFT_WOOD: 1146,
    ABIDOS_WOOD: 13,
}

lumber_prices = get_lumber_prices()
prices = ac.build_calculation_prices(lumber_prices)

required_materials = ac.get_required_materials(craft_count)
missing_materials = ac.get_missing_materials(
        owned_materials,
        required_materials
    )
remaining_materials = ac.calculate_remaining_materials(owned_materials,required_materials)
exchangeable_materials = ac.calculate_exchangeable_materials(owned_materials,required_materials)
required_powder_info = ac.calculate_required_abidos_powder(
        missing_materials
    )

print_json(required_powder_info)