from src.exchange_calculator import (
    apply_abidos_exchange,
    calculate_exchangeable_materials,
    calculate_powder_exchange_plans,
    calculate_required_abidos_powder,
    get_used_materials_from_exchange_plan,
)
from src.material_utils import (
    calculate_material_value,
    calculate_remaining_materials,
    can_craft,
    get_missing_materials,
    get_required_materials,
)
from src.price_utils import calculate_missing_cost


def calculate_direct_purchase_plan(
        owned_materials: dict, 
        prices: dict, 
        craft_count: int = 40
        ) -> dict:
    """
    직접 구매만 하여 제작 가능한 계획을 반환
    """
    required_materials = get_required_materials(craft_count)
    if can_craft(owned_materials, required_materials):
        after_craft_materials = calculate_remaining_materials(
            owned_materials, 
            required_materials
            )
        return {
    "제작횟수": craft_count,
    "플랜이름": "보유재료만으로 제작",
    "구매전 제작가능여부": True,
    "필요재료": required_materials,
    "부족한재료": {},
    "구매계획": {},
    "구매후재료": owned_materials.copy(),
    "제작가능여부": True,
    "제작후 남은재료": after_craft_materials,
    "사용재료": {},
    "사용재료가치" : 0,
    "총비용": 0,
}
    missing_materials = get_missing_materials(owned_materials, required_materials)
    purchase_plan = calculate_missing_cost(prices, missing_materials)

    total_cost = sum(item["비용"] for item in purchase_plan.values())

    after_purchase_materials = owned_materials.copy()
    for name, plan in purchase_plan.items():
        after_purchase_materials[name] = (
            after_purchase_materials.get(name, 0)
            + plan["구매재료"]
        )
    after_craft_materials = calculate_remaining_materials(
        after_purchase_materials,
        required_materials
        )

    return {
    "제작횟수": craft_count,
    "플랜이름": "부족재료 모두구매 후 제작",
    "구매전 제작가능여부": False,
    "필요재료": required_materials,
    "부족한재료": missing_materials,
    "구매계획": purchase_plan,
    "구매후재료": after_purchase_materials,
    "제작가능여부": can_craft(
        after_purchase_materials,
        required_materials
    ),
    "제작후 남은재료": after_craft_materials,
    "사용재료": {},
    "사용재료가치" : 0,
    "총비용": total_cost
}


def calculate_exchange_only_candidates(
    owned_materials: dict,
    prices:dict,
    craft_count: int = 40
) -> dict:
    '''
    단일 재료 교환만으로 제작 가능한 후보들을 반환한다.
    '''
    required_materials = get_required_materials(craft_count)

    if can_craft(owned_materials, required_materials):
        after_craft_materials = calculate_remaining_materials(
            owned_materials,
            required_materials
        )

        return {
            "제작횟수": craft_count,
            "플랜이름": "단일재료 교환 제작 후보",
            "교환전 제작가능여부": True,
            "필요재료": required_materials,
            "후보플랜들": [
                {
                    "제작횟수": craft_count,
                    "플랜이름": "보유재료만으로 제작",
                    "필요재료": required_materials,
                    "교환계획": None,
                    "교환후재료": owned_materials.copy(),
                    "교환후부족재료": {},
                    "제작가능여부": True,
                    "제작후 남은재료": after_craft_materials,
                    "사용재료": {},
                    "사용재료가치" : 0,
                    "총비용": 0
                }
            ],
        }

    missing_materials = get_missing_materials(
        owned_materials,
        required_materials
    )

    exchangeable_materials = calculate_exchangeable_materials(
        owned_materials,
        required_materials
    )

    required_powder_info = calculate_required_abidos_powder(
        missing_materials
    )

    exchange_plans = calculate_powder_exchange_plans(
        exchangeable_materials,
        required_powder_info
    )

    candidate_plans = []

    for material_name, exchange_plan in exchange_plans.items():
        if not exchange_plan["가능여부"]:
            continue

        after_exchange_materials = apply_abidos_exchange(
            owned_materials,
            exchange_plan
        )

        can_craft_after_exchange = can_craft(
            after_exchange_materials,
            required_materials
        )

        if can_craft_after_exchange:
            after_craft_materials = calculate_remaining_materials(
                after_exchange_materials,
                required_materials
            )
            after_exchange_missing = {}
            total_cost = 0
        else:
            after_craft_materials = None
            after_exchange_missing = get_missing_materials(
                after_exchange_materials,
                required_materials
            )
            total_cost = None

        used_materials = get_used_materials_from_exchange_plan(exchange_plan)

        candidate_plans.append({
            "제작횟수": craft_count,
            "플랜이름": f"{material_name} 단일교환 제작",
            "필요재료": required_materials,
            "부족한재료": missing_materials,
            "필요가루정보": required_powder_info,
            "교환계획": exchange_plan,
            "교환후재료": after_exchange_materials,
            "교환후부족재료": after_exchange_missing,
            "제작가능여부": can_craft_after_exchange,
            "제작후 남은재료": after_craft_materials,
            "사용재료": used_materials,
            "사용재료가치": calculate_material_value(used_materials, prices),
            "총비용": total_cost,
        })

    return {
        "제작횟수": craft_count,
        "플랜이름": "단일재료 교환 제작 후보",
        "교환전 제작가능여부": False,
        "필요재료": required_materials,
        "부족한재료": missing_materials,
        "필요가루정보": required_powder_info,
        "교환계획들": exchange_plans,
        "후보플랜들": candidate_plans,
    }


def calculate_exchange_then_purchase_candidates(
    owned_materials: dict,
    prices: dict,
    craft_count: int = 40
) -> dict:
    '''
    단일 재료 교환 후 부족분을 구매하는 후보들을 반환한다.
    '''
    required_materials = get_required_materials(craft_count)

    if can_craft(owned_materials, required_materials):
        after_craft_materials = calculate_remaining_materials(
            owned_materials,
            required_materials
        )

        return {
            "제작횟수": craft_count,
            "플랜이름": "단일재료 교환 후 부족분 구매 후보",
            "구매전 제작가능여부": True,
            "필요재료": required_materials,
            "후보플랜들": [
                {
                    "제작횟수": craft_count,
                    "플랜이름": "보유재료만으로 제작",
                    "필요재료": required_materials,
                    "교환계획": None,
                    "구매계획": {},
                    "구매후재료": owned_materials.copy(),
                    "제작가능여부": True,
                    "제작후 남은재료": after_craft_materials,
                    "사용재료": {},
                    "사용재료가치":0,
                    "총비용": 0,
                }
            ],
        }

    missing_materials = get_missing_materials(
        owned_materials,
        required_materials
    )

    required_powder_info = calculate_required_abidos_powder(
        missing_materials
    )

    exchangeable_materials = calculate_exchangeable_materials(
        owned_materials,
        required_materials
    )

    powder_exchange_plans = calculate_powder_exchange_plans(
        exchangeable_materials,
        required_powder_info
    )

    candidate_plans = []

    for material_name, exchange_plan in powder_exchange_plans.items():
        if exchange_plan["획득아비도스목재"] <= 0:
            continue

        after_exchange_materials = apply_abidos_exchange(
            owned_materials,
            exchange_plan
        )

        after_exchange_missing = get_missing_materials(
            after_exchange_materials,
            required_materials
        )

        purchase_plan = calculate_missing_cost(
            prices,
            after_exchange_missing
        )

        after_purchase_materials = after_exchange_materials.copy()

        for name, plan in purchase_plan.items():
            after_purchase_materials[name] = (
                after_purchase_materials.get(name, 0)
                + plan["구매재료"]
            )

        can_craft_after_purchase = can_craft(
            after_purchase_materials,
            required_materials
        )

        if can_craft_after_purchase:
            after_craft_materials = calculate_remaining_materials(
                after_purchase_materials,
                required_materials
            )
        else:
            after_craft_materials = None

        used_materials = get_used_materials_from_exchange_plan(exchange_plan)

        total_cost = sum(
            item["비용"]
            for item in purchase_plan.values()
        )
        candidate_plans.append({
            "제작횟수": craft_count,
            "플랜이름": f"{material_name} 교환 후 부족분 구매",
            "필요재료": required_materials,
            "부족한재료": missing_materials,
            "필요가루정보": required_powder_info,
            "교환계획": exchange_plan,
            "교환후재료": after_exchange_materials,
            "교환후부족재료": after_exchange_missing,
            "구매계획": purchase_plan,
            "구매후재료": after_purchase_materials,
            "제작가능여부": can_craft_after_purchase,
            "제작후 남은재료": after_craft_materials,
            "사용재료": used_materials,
            "사용재료가치": calculate_material_value(used_materials, prices),
            "총비용": total_cost,
        })

    return {
        "제작횟수": craft_count,
        "플랜이름": "단일재료 교환 후 부족분 구매 후보",
        "구매전 제작가능여부": False,
        "필요재료": required_materials,
        "부족한재료": missing_materials,
        "필요가루정보": required_powder_info,
        "교환계획들": powder_exchange_plans,
        "후보플랜들": candidate_plans,
    }
