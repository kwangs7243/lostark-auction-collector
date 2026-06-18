from src.constants import (
    ABIDOS_WOOD,
    EXCHANGE_RECIPES,
    POWDER_TO_ABIDOS_RECIPE,
    PURCHASE_UNIT,
    SOFT_WOOD,
    WOOD,
)


def _usable_prices(price_info: dict) -> list[int | float]:
    """API 가격 정보 중 계산에 사용할 수 있는 숫자 가격만 추린다."""
    candidates = [
        price_info.get("최저가"),
        price_info.get("최근가"),
        price_info.get("전일가"),
    ]
    return [
        price
        for price in candidates
        if isinstance(price, (int, float)) and price > 0
    ]


def build_calculation_prices(raw_prices: dict) -> dict:
    """API 원본 가격에서 실제 계산에 사용할 보수적인 가격표를 만든다."""
    prices = {}

    for name, price_info in raw_prices.items():
        candidates = _usable_prices(price_info)
        if candidates:
            prices[name] = max(candidates)

    validate_required_prices(prices)
    return prices


def validate_required_prices(prices: dict) -> None:
    """제작 계산에 반드시 필요한 재료 가격이 모두 있는지 확인한다."""
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
        raise ValueError(f"필수 가격 정보가 없습니다: {missing_names}")


def calculate_powder_unit_cost(
    material_name: str,
    prices: dict,
) -> float:
    """특정 재료를 생활의 가루 1개로 바꿀 때의 환산 비용을 계산한다."""
    recipe = EXCHANGE_RECIPES[material_name]
    bundle_price = prices[material_name]

    material_cost = bundle_price / PURCHASE_UNIT * recipe["required_material"]
    return material_cost / recipe["gained_powder"]


def get_priority_order(prices: dict) -> list[str]:
    """생활의 가루 환산 비용이 낮은 재료 순서로 정렬한다."""
    return sorted(
        EXCHANGE_RECIPES,
        key=lambda material_name: calculate_powder_unit_cost(
            material_name,
            prices,
        ),
    )


def calculate_abidos_exchange_unit_cost(
    material_name: str,
    prices: dict,
) -> float:
    """특정 재료를 구매해 교환할 때 아비도스 목재 1개당 비용을 계산한다."""
    powder_unit_cost = calculate_powder_unit_cost(material_name, prices)
    required_powder = POWDER_TO_ABIDOS_RECIPE["required_powder"]
    gained_abidos = POWDER_TO_ABIDOS_RECIPE["gained_abidos"]
    return powder_unit_cost * required_powder / gained_abidos


def compare_abidos_purchase_vs_exchange(prices: dict) -> dict:
    """아비도스 목재 직접 구매와 재료 구매 후 교환의 단가를 비교한다."""
    priority_order = get_priority_order(prices)
    cheapest_material = priority_order[0]

    exchange_unit_cost = calculate_abidos_exchange_unit_cost(
        cheapest_material,
        prices,
    )
    direct_abidos_price = prices[ABIDOS_WOOD] / PURCHASE_UNIT
    should_buy_directly = direct_abidos_price <= exchange_unit_cost

    return {
        "직접구매추천": should_buy_directly,
        "추천방식": "직접구매" if should_buy_directly else "교환",
        "직접구매단가": direct_abidos_price,
        "교환환산단가": exchange_unit_cost,
        "가루최저재료": cheapest_material,
        "가루1개비용": calculate_powder_unit_cost(cheapest_material, prices),
        "우선순위": priority_order,
    }
