from src.constants import (
    EXCHANGE_RECIPES,
    WOOD,
    SOFT_WOOD,
    ABIDOS_WOOD,
    POWDER_TO_ABIDOS_RECIPE
)
from src.material_utils import round_up_to_unit


# 제작 책임없는
# 순수 가격계산
def build_calculation_prices(raw_prices: dict) -> dict:
    '''
    계산에 사용할 가격정보를 가공한다.
    '''
    prices = {}

    for name, price_info in raw_prices.items():
        prices[name] = max(
            price_info["최저가"],
            price_info["최근가"]
        )

    validate_required_prices(prices)

    return prices


def validate_required_prices(prices: dict) -> None:
    '''
    제작 계산에 필요한 필수 가격 정보가 있는지 검증한다.
    '''
    required_names = [
        WOOD,
        SOFT_WOOD,
        ABIDOS_WOOD,
    ]

    missing_names = [
        name for name in required_names
        if name not in prices
    ]

    if missing_names:
        raise ValueError(
            f"필수 가격 정보가 없습니다: {missing_names}"
        )


def calculate_missing_cost(
    prices: dict,
    missing_materials: dict
) -> dict:
    '''
    제작에 부족한 재료의 구매 가격을 계산하여 반환한다.
    '''
    result = {}

    for name, missing_amount in missing_materials.items():
        price = prices[name]
        buy_amount = round_up_to_unit(missing_amount, 100)

        result[name] = {
            "부족한재료": missing_amount,
            "구매재료": buy_amount,
            "비용": buy_amount * price // 100
        }

    return result


def calculate_powder_unit_cost(
    material_name: str,
    prices: dict
) -> float:
    '''
    특정 재료로 가루 1개를 만들 때의 실제 거래소 기준 비용을 계산한다.
    거래소 가격은 100개 묶음 기준이다.
    '''
    recipe = EXCHANGE_RECIPES[material_name]
    bundle_price = prices[material_name]

    return (
        bundle_price
        / 100
        * recipe["필요재료"]
        / recipe["획득가루"]
    )


def get_priority_order(prices: dict) -> list[str]:
    '''
    가루 1개당 비용이 낮은 재료 순서로 정렬한다.
    '''
    return sorted(
        EXCHANGE_RECIPES,
        key=lambda material_name: calculate_powder_unit_cost(
            material_name,
            prices
        )
    )

def compare_abidos_purchase_vs_exchange(prices: dict) -> dict:
    '''
    아비도스 목재를 직접 구매할지
    재료목재를 구매해서 교환하여 얻을지 계산하여 반환
    '''
    priority_order = get_priority_order(prices)
    cheapest_material = priority_order[0]

    powder_unit_cost = calculate_powder_unit_cost(
        cheapest_material,
        prices
    )

    powder_cost_per_abidos = (
        powder_unit_cost
        * POWDER_TO_ABIDOS_RECIPE["필요재료"]
        / POWDER_TO_ABIDOS_RECIPE["획득재료"]
    )

    direct_abidos_price = prices[ABIDOS_WOOD] / 100

    should_buy_directly = direct_abidos_price <= powder_cost_per_abidos

    return {
        "직접구매추천": should_buy_directly,
        "추천방식": "직접구매" if should_buy_directly else "교환",
        "직접구매단가": direct_abidos_price,
        "교환환산단가": powder_cost_per_abidos,
        "가루최저재료": cheapest_material,
        "가루1개비용": powder_unit_cost,
        "우선순위": priority_order,
    }