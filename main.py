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


def main() -> None:
    craft_count = 40

    owned_materials = {
        WOOD: 31812,
        SOFT_WOOD: 1146,
        ABIDOS_WOOD: 13,
    }

    lumber_prices = get_lumber_prices()
    prices = ac.build_calculation_prices(lumber_prices)

    direct_purchase_plan = ac.calculate_direct_purchase_plan(
        owned_materials=owned_materials,
        prices=prices,
        craft_count=craft_count
    )

    exchange_only_plan = ac.calculate_exchange_only_plan(
        owned_materials=owned_materials,
        craft_count=craft_count
    )

    exchange_then_purchase_plan = ac.calculate_exchange_then_purchase_plan(
        owned_materials=owned_materials,
        prices=prices,
        craft_count=craft_count
    )
    print("=== 직접 구매 플랜 ===")
    print_json(direct_purchase_plan)

    print("\n=== 보유재료 교환 플랜 ===")
    print_json(exchange_only_plan)

    print("\n=== 보유재료 교환 후 구매 플랜 ===")
    print_json(exchange_then_purchase_plan)


if __name__ == "__main__":
    main()



    
    


