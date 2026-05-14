from src.exchange_calculator import (
    apply_abidos_exchange,
    calculate_exchangeable_materials,
    calculate_mixed_powder_exchange_plan,
    calculate_required_abidos_powder,
)
from src.material_utils import (
    calculate_material_value,
    calculate_remaining_materials,
    can_craft,
    get_missing_materials,
    get_required_materials,
)
from src.price_utils import get_priority_order
from src.purchase_calculator import (
    apply_smart_purchase_plan,
    build_smart_purchase_plan,
)


# 여러 계산들을 수집하여 제작 가능한 플랜을 만든다.


def _build_owned_only_result(
    owned_materials: dict,
    required_materials: dict,
    craft_count: int,
    plan_name: str = "보유재료만으로 제작"
) -> dict:
    '''
    이미 보유재료만으로 제작 가능한 경우의 공통 결과를 만든다.
    '''
    after_craft_materials = calculate_remaining_materials(
        owned_materials,
        required_materials
    )

    return {
        "제작횟수": craft_count,
        "플랜이름": plan_name,
        "필요재료": required_materials,
        "부족한재료": {},
        "필요가루정보": {},
        "교환가능재료": {},
        "교환계획": None,
        "교환후재료": owned_materials.copy(),
        "교환후부족재료": {},
        "구매계획": {},
        "구매후재료": owned_materials.copy(),
        "제작가능여부": True,
        "제작후남은재료": after_craft_materials,
        "사용재료": {},
        "사용재료가치": 0,
        "구매비용": 0,
        "총비용": 0,
    }


def calculate_direct_purchase_plan(
    owned_materials: dict,
    prices: dict,
    craft_count: int = 40
) -> dict:
    '''
    부족재료를 구매해서 제작 가능한 계획을 반환한다.

    기존 함수명은 유지하지만,
    아비도스 목재는 직접 구매와 교환 구매 중 더 싼 방식을 선택한다.
    '''
    required_materials = get_required_materials(craft_count)

    if can_craft(owned_materials, required_materials):
        return _build_owned_only_result(
            owned_materials,
            required_materials,
            craft_count
        )

    missing_materials = get_missing_materials(
        owned_materials,
        required_materials
    )

    purchase_plan = build_smart_purchase_plan(
        prices,
        missing_materials
    )

    after_purchase_materials = apply_smart_purchase_plan(
        owned_materials,
        purchase_plan
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

    return {
        "제작횟수": craft_count,
        "플랜이름": "부족재료 스마트 구매 후 제작",
        "필요재료": required_materials,
        "부족한재료": missing_materials,
        "필요가루정보": purchase_plan.get("필요가루정보", {}),
        "교환가능재료": {},
        "교환계획": purchase_plan.get("구매후교환계획"),
        "교환후재료": None,
        "교환후부족재료": {},
        "구매계획": purchase_plan,
        "구매후재료": after_purchase_materials,
        "제작가능여부": can_craft_after_purchase,
        "제작후남은재료": after_craft_materials,
        "사용재료": {},
        "사용재료가치": 0,
        "구매비용": purchase_plan["총비용"],
        "총비용": purchase_plan["총비용"],
    }


def calculate_mixed_exchange_only_plan(
    owned_materials: dict,
    prices: dict,
    craft_count: int = 40
) -> dict:
    '''
    보유 잉여재료를 우선순위에 따라 혼합 교환하여 제작 가능한 계획을 반환한다.
    '''
    required_materials = get_required_materials(craft_count)

    if can_craft(owned_materials, required_materials):
        return _build_owned_only_result(
            owned_materials,
            required_materials,
            craft_count
        )

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

    priority_order = get_priority_order(prices)

    exchange_plan = calculate_mixed_powder_exchange_plan(
        exchangeable_materials,
        required_powder_info,
        priority_order
    )

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

    used_materials = exchange_plan["사용재료"]

    return {
        "제작횟수": craft_count,
        "플랜이름": "보유 잉여재료 혼합교환 제작",
        "필요재료": required_materials,
        "부족한재료": missing_materials,
        "필요가루정보": required_powder_info,
        "교환가능재료": exchangeable_materials,
        "교환계획": exchange_plan,
        "교환후재료": after_exchange_materials,
        "교환후부족재료": after_exchange_missing,
        "구매계획": {},
        "구매후재료": after_exchange_materials,
        "제작가능여부": can_craft_after_exchange,
        "제작후남은재료": after_craft_materials,
        "사용재료": used_materials,
        "사용재료가치": calculate_material_value(used_materials, prices),
        "구매비용": 0,
        "총비용": total_cost,
    }


def calculate_mixed_exchange_then_purchase_plan(
    owned_materials: dict,
    prices: dict,
    craft_count: int = 40
) -> dict:
    '''
    보유 잉여재료를 우선순위에 따라 혼합 교환한 뒤,
    부족한 재료를 스마트 구매하여 제작 가능한 계획을 반환한다.
    '''
    required_materials = get_required_materials(craft_count)

    if can_craft(owned_materials, required_materials):
        return _build_owned_only_result(
            owned_materials,
            required_materials,
            craft_count
        )

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

    priority_order = get_priority_order(prices)

    exchange_plan = calculate_mixed_powder_exchange_plan(
        exchangeable_materials,
        required_powder_info,
        priority_order
    )

    after_exchange_materials = apply_abidos_exchange(
        owned_materials,
        exchange_plan
    )

    after_exchange_missing = get_missing_materials(
        after_exchange_materials,
        required_materials
    )

    purchase_plan = build_smart_purchase_plan(
        prices,
        after_exchange_missing
    )

    after_purchase_materials = apply_smart_purchase_plan(
        after_exchange_materials,
        purchase_plan
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

    used_materials = exchange_plan["사용재료"]

    purchase_cost = purchase_plan["총비용"]

    used_material_value = calculate_material_value(
        used_materials,
        prices
    )

    return {
        "제작횟수": craft_count,
        "플랜이름": "보유 잉여재료 혼합교환 후 스마트 구매",
        "필요재료": required_materials,
        "부족한재료": missing_materials,
        "필요가루정보": required_powder_info,
        "교환가능재료": exchangeable_materials,
        "교환계획": exchange_plan,
        "교환후재료": after_exchange_materials,
        "교환후부족재료": after_exchange_missing,
        "구매계획": purchase_plan,
        "구매후재료": after_purchase_materials,
        "제작가능여부": can_craft_after_purchase,
        "제작후남은재료": after_craft_materials,
        "사용재료": used_materials,
        "사용재료가치": used_material_value,
        "구매비용": purchase_cost,
        "총비용": purchase_cost,
    }
