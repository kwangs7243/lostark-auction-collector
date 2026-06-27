import json

import src.abidos_calculator as ac
from src.constants import (
    ABIDOS_WOOD,
    CATEGORY_CODES,
    DEFAULT_RECIPE_KEY,
    RECIPES,
    SOFT_WOOD,
    WOOD,
)
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


def print_json(data) -> None:
    """dict 또는 list 데이터를 한글이 깨지지 않는 JSON 형태로 출력한다."""
    print(json.dumps(data, ensure_ascii=False, indent=4))


def print_plan_summary(plan: dict) -> None:
    """후보 플랜의 핵심 비교 정보만 간단히 출력한다."""
    print(f"- {plan['플랜이름']}")
    print(f"  제작가능: {plan['제작가능여부']}")
    print(f"  구매비용: {plan['구매비용']}")
    print(f"  사용재료가치: {plan['사용재료가치']}")


def main() -> None:
    """보유 재료와 제작 횟수를 기준으로 후보 플랜을 만들고 최적 플랜을 출력한다."""
    craft_count = 40

    owned_materials = {
        WOOD: 27551,
        SOFT_WOOD: 3818,
        ABIDOS_WOOD: 1045,
    }

    raw_prices = get_market_prices()
    prices = ac.build_calculation_prices(raw_prices)
    recipe = RECIPES[DEFAULT_RECIPE_KEY]
    candidate_plans = ac.generate_candidate_plans(
        owned_materials=owned_materials,
        prices=prices,
        craft_count=craft_count,
        recipe=recipe,
    )
    best_plan = ac.select_best_plan(candidate_plans)

    print("\n=== 후보 플랜 요약 ===")
    for plan in candidate_plans:
        print_plan_summary(plan)

    print("\n=== 최종 추천 플랜 ===")
    print_json(best_plan)


if __name__ == "__main__":
    main()
