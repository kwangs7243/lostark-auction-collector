from src.constants import (
    ABIDOS_WOOD,
    EXCHANGE_RECIPES,
    POWDER_TO_ABIDOS_RECIPE,
    PURCHASE_UNIT,
)
from src.exchange_calculator import calculate_required_abidos_powder
from src.material_utils import round_up_to_unit
from src.price_utils import compare_abidos_purchase_vs_exchange, get_priority_order


def calculate_missing_cost(
    prices: dict,
    missing_materials: dict,
) -> dict:
    """부족한 재료를 거래소에서 직접 구매할 때의 비용 계획을 만든다."""
    result = {}

    for name, missing_amount in missing_materials.items():
        if missing_amount <= 0:
            continue

        price = prices[name]
        buy_amount = round_up_to_unit(missing_amount, PURCHASE_UNIT)

        result[name] = {
            "부족한재료": missing_amount,
            "구매재료": buy_amount,
            "비용": buy_amount * price // PURCHASE_UNIT,
        }

    return result


def calculate_purchase_cost(purchase_plan: dict) -> int:
    """구매 계획에 들어 있는 모든 항목의 비용을 합산한다."""
    return sum(
        item["비용"]
        for item in purchase_plan.values()
    )


def apply_purchase_plan(
    owned_materials: dict,
    purchase_plan: dict,
) -> dict:
    """구매 계획으로 늘어난 재료 수량을 보유 재료에 반영한다."""
    after_purchase_materials = owned_materials.copy()

    for name, plan in purchase_plan.items():
        after_purchase_materials[name] = (
            after_purchase_materials.get(name, 0)
            + plan["구매재료"]
        )

    return after_purchase_materials


def build_abidos_direct_purchase_plan(
    prices: dict,
    missing_abidos_wood: int,
) -> dict:
    """부족한 아비도스 목재를 직접 구매하는 후보 계획을 만든다."""
    direct_purchase_plan = calculate_missing_cost(
        prices,
        {ABIDOS_WOOD: missing_abidos_wood},
    )

    return {
        "구매방식": "아비도스 직접구매",
        "직접구매계획": direct_purchase_plan,
        "교환용구매계획": {},
        "필요가루정보": {},
        "구매후교환계획": None,
        "총비용": calculate_purchase_cost(direct_purchase_plan),
    }


def build_abidos_exchange_purchase_plan(
    prices: dict,
    missing_abidos_wood: int,
    material_name: str,
) -> dict:
    """재료를 구매해 가루로 교환한 뒤 아비도스 목재를 얻는 후보 계획을 만든다."""
    required_powder_info = calculate_required_abidos_powder({
        ABIDOS_WOOD: missing_abidos_wood,
    })
    recipe = EXCHANGE_RECIPES[material_name]
    required_powder = required_powder_info["필요한가루"]
    exchange_count = round_up_to_unit(
        required_powder,
        recipe["gained_powder"],
    ) // recipe["gained_powder"]
    used_amount = exchange_count * recipe["required_material"]
    buy_amount = round_up_to_unit(used_amount, PURCHASE_UNIT)
    gained_powder = exchange_count * recipe["gained_powder"]
    possible_abidos_wood = (
        gained_powder
        // POWDER_TO_ABIDOS_RECIPE["required_powder"]
        * POWDER_TO_ABIDOS_RECIPE["gained_abidos"]
    )
    gained_abidos_wood = min(
        possible_abidos_wood,
        required_powder_info["보정된 아비도스 목재"],
    )

    exchange_purchase_plan = {
        material_name: {
            "부족한재료": used_amount,
            "구매재료": buy_amount,
            "비용": buy_amount * prices[material_name] // PURCHASE_UNIT,
        }
    }
    exchange_plan = {
        "우선순위": [material_name],
        "필요가루": required_powder,
        "획득가루": gained_powder,
        "남은필요가루": max(required_powder - gained_powder, 0),
        "아비도스목재교환횟수": (
            gained_abidos_wood
            // POWDER_TO_ABIDOS_RECIPE["gained_abidos"]
        ),
        "필요아비도스목재": required_powder_info["보정된 아비도스 목재"],
        "획득아비도스목재": gained_abidos_wood,
        "사용재료": {
            material_name: used_amount,
        },
        "교환상세": [
            {
                "재료이름": material_name,
                "교환횟수": exchange_count,
                "사용재료수량": used_amount,
                "획득가루": gained_powder,
                "교환후남은필요가루": max(required_powder - gained_powder, 0),
            }
        ],
        "가능여부": gained_abidos_wood >= required_powder_info["보정된 아비도스 목재"],
    }

    return {
        "구매방식": f"{material_name} 구매 후 교환",
        "직접구매계획": {},
        "교환용구매계획": exchange_purchase_plan,
        "필요가루정보": required_powder_info,
        "구매후교환계획": exchange_plan,
        "총비용": calculate_purchase_cost(exchange_purchase_plan),
    }


def build_abidos_fill_purchase_candidates(
    prices: dict,
    missing_abidos_wood: int,
) -> list[dict]:
    """아비도스 목재 부족분을 채우는 모든 구매 후보를 생성한다."""
    if missing_abidos_wood <= 0:
        return [{
            "구매방식": "아비도스 추가구매 없음",
            "직접구매계획": {},
            "교환용구매계획": {},
            "필요가루정보": {},
            "구매후교환계획": None,
            "총비용": 0,
        }]

    candidates = [
        build_abidos_direct_purchase_plan(prices, missing_abidos_wood),
    ]

    for material_name in get_priority_order(prices):
        candidates.append(
            build_abidos_exchange_purchase_plan(
                prices,
                missing_abidos_wood,
                material_name,
            )
        )

    return candidates


def build_smart_purchase_plan(
    prices: dict,
    missing_materials: dict,
) -> dict:
    """부족 재료 구매 계획 중 아비도스 충당 방식을 비용 기준으로 선택한다."""
    price_compare = compare_abidos_purchase_vs_exchange(prices)
    missing_abidos_wood = missing_materials.get(ABIDOS_WOOD, 0)
    normal_missing_materials = {
        name: amount
        for name, amount in missing_materials.items()
        if name != ABIDOS_WOOD and amount > 0
    }

    normal_purchase_plan = calculate_missing_cost(
        prices,
        normal_missing_materials,
    )
    normal_purchase_cost = calculate_purchase_cost(normal_purchase_plan)

    abidos_candidates = build_abidos_fill_purchase_candidates(
        prices,
        missing_abidos_wood,
    )
    best_abidos_plan = min(
        abidos_candidates,
        key=lambda plan: plan["총비용"],
    )

    total_cost = normal_purchase_cost + best_abidos_plan["총비용"]

    return {
        "구매방식": best_abidos_plan["구매방식"],
        "가격비교": price_compare,
        "직접구매계획": {
            **normal_purchase_plan,
            **best_abidos_plan["직접구매계획"],
        },
        "교환용구매계획": best_abidos_plan["교환용구매계획"],
        "필요가루정보": best_abidos_plan["필요가루정보"],
        "구매후교환계획": best_abidos_plan["구매후교환계획"],
        "직접구매비용": normal_purchase_cost + calculate_purchase_cost(
            best_abidos_plan["직접구매계획"],
        ),
        "교환용구매비용": calculate_purchase_cost(
            best_abidos_plan["교환용구매계획"],
        ),
        "총비용": total_cost,
        "아비도스구매후보": abidos_candidates,
    }


def apply_smart_purchase_plan(
    owned_materials: dict,
    smart_purchase_plan: dict,
) -> dict:
    """스마트 구매 계획과 구매 후 교환 계획을 보유 재료에 차례로 반영한다."""
    after_purchase_materials = owned_materials.copy()

    after_purchase_materials = apply_purchase_plan(
        after_purchase_materials,
        smart_purchase_plan.get("직접구매계획", {}),
    )
    after_purchase_materials = apply_purchase_plan(
        after_purchase_materials,
        smart_purchase_plan.get("교환용구매계획", {}),
    )

    exchange_plan = smart_purchase_plan.get("구매후교환계획")

    if exchange_plan:
        for material_name, used_amount in exchange_plan["사용재료"].items():
            after_purchase_materials[material_name] = (
                after_purchase_materials.get(material_name, 0)
                - used_amount
            )

        after_purchase_materials[ABIDOS_WOOD] = (
            after_purchase_materials.get(ABIDOS_WOOD, 0)
            + exchange_plan["획득아비도스목재"]
        )

    return after_purchase_materials
