from src.constants import (
    ABIDOS_WOOD,
    EXCHANGE_RECIPES,
    POWDER_TO_ABIDOS_RECIPE,
    SOFT_WOOD,
    WOOD,
)
from src.material_utils import round_up_to_unit


def calculate_exchangeable_materials(
    owned_materials: dict,
    required_materials: dict,
) -> dict:
    """제작 필요분을 제외하고 교환에 사용할 수 있는 잉여 재료를 계산한다."""
    result = {}

    for name in [WOOD, SOFT_WOOD]:
        owned_amount = owned_materials.get(name, 0)
        required_amount = required_materials.get(name, 0)
        result[name] = max(owned_amount - required_amount, 0)

    return result


def calculate_required_abidos_powder(missing_materials: dict) -> dict:
    """부족한 아비도스 목재를 교환으로 채우는 데 필요한 가루를 계산한다."""
    missing_abidos_wood = missing_materials.get(ABIDOS_WOOD, 0)
    adjusted_abidos_wood = round_up_to_unit(
        missing_abidos_wood,
        POWDER_TO_ABIDOS_RECIPE["gained_abidos"],
    )
    exchange_count = (
        adjusted_abidos_wood
        // POWDER_TO_ABIDOS_RECIPE["gained_abidos"]
    )
    required_powder = exchange_count * POWDER_TO_ABIDOS_RECIPE["required_powder"]

    return {
        "부족한 아비도스 목재": missing_abidos_wood,
        "보정된 아비도스 목재": adjusted_abidos_wood,
        "교환필요횟수": exchange_count,
        "필요한가루": required_powder,
    }


def _build_empty_exchange_plan(
    required_powder: int,
    required_abidos_wood: int,
    priority_order: list[str],
) -> dict:
    """교환할 필요가 없을 때 사용하는 빈 교환 계획을 만든다."""
    return {
        "우선순위": priority_order,
        "필요가루": required_powder,
        "획득가루": 0,
        "남은필요가루": required_powder,
        "아비도스목재교환횟수": 0,
        "필요아비도스목재": required_abidos_wood,
        "획득아비도스목재": 0,
        "사용재료": {},
        "교환상세": [],
        "가능여부": required_powder <= 0,
    }


def calculate_mixed_powder_exchange_plan(
    exchangeable_materials: dict,
    required_powder_info: dict,
    priority_order: list[str],
) -> dict:
    """잉여 재료를 우선순위대로 섞어 생활의 가루 교환 계획을 만든다."""
    original_required_powder = required_powder_info["필요한가루"]
    required_abidos_wood = required_powder_info["보정된 아비도스 목재"]

    if original_required_powder <= 0:
        return _build_empty_exchange_plan(
            original_required_powder,
            required_abidos_wood,
            priority_order,
        )

    remaining_required_powder = original_required_powder
    total_gained_powder = 0
    exchange_details = []
    used_materials = {}

    for material_name in priority_order:
        if remaining_required_powder <= 0:
            break

        recipe = EXCHANGE_RECIPES[material_name]
        material_amount = exchangeable_materials.get(material_name, 0)
        possible_exchange_count = material_amount // recipe["required_material"]
        required_exchange_count = round_up_to_unit(
            remaining_required_powder,
            recipe["gained_powder"],
        ) // recipe["gained_powder"]
        exchange_count = min(possible_exchange_count, required_exchange_count)

        if exchange_count <= 0:
            continue

        used_amount = exchange_count * recipe["required_material"]
        gained_powder = exchange_count * recipe["gained_powder"]
        remaining_required_powder = max(
            remaining_required_powder - gained_powder,
            0,
        )
        total_gained_powder += gained_powder
        used_materials[material_name] = used_amount
        exchange_details.append({
            "재료이름": material_name,
            "교환횟수": exchange_count,
            "사용재료수량": used_amount,
            "획득가루": gained_powder,
            "교환후남은필요가루": remaining_required_powder,
        })

    possible_abidos_wood = (
        total_gained_powder
        // POWDER_TO_ABIDOS_RECIPE["required_powder"]
        * POWDER_TO_ABIDOS_RECIPE["gained_abidos"]
    )
    gained_abidos_wood = min(possible_abidos_wood, required_abidos_wood)
    abidos_wood_exchange_count = (
        gained_abidos_wood
        // POWDER_TO_ABIDOS_RECIPE["gained_abidos"]
    )

    return {
        "우선순위": priority_order,
        "필요가루": original_required_powder,
        "획득가루": total_gained_powder,
        "남은필요가루": remaining_required_powder,
        "아비도스목재교환횟수": abidos_wood_exchange_count,
        "필요아비도스목재": required_abidos_wood,
        "획득아비도스목재": gained_abidos_wood,
        "사용재료": used_materials,
        "교환상세": exchange_details,
        "가능여부": remaining_required_powder <= 0,
    }


def apply_abidos_exchange(
    owned_materials: dict,
    exchange_plan: dict,
) -> dict:
    """아비도스 교환 계획을 보유 재료 수량에 반영한다."""
    after_exchange_materials = owned_materials.copy()

    for material_name, used_amount in exchange_plan.get("사용재료", {}).items():
        after_exchange_materials[material_name] = (
            after_exchange_materials.get(material_name, 0)
            - used_amount
        )

    after_exchange_materials[ABIDOS_WOOD] = (
        after_exchange_materials.get(ABIDOS_WOOD, 0)
        + exchange_plan.get("획득아비도스목재", 0)
    )

    return after_exchange_materials
