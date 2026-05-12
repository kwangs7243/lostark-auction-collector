from src.constants import (
    EXCHANGE_RECIPES,
    POWDER_TO_ABIDOS_RECIPE,
    WOOD,
    SOFT_WOOD,
    ABIDOS_WOOD,
)
from src.material_utils import round_up_to_unit

# 교환에 필요한 계산
# constants 교환레시피를 알고 이를 책임하여 교환시스템구현


def calculate_exchangeable_materials(
    owned_materials: dict,
    required_materials: dict
) -> dict:
    '''
    제작에 필요한 갯수를 제외한 목재와 부드러운 목재의
    수량을 반환
    '''
    result = {}

    for name in [WOOD, SOFT_WOOD]:
        owned_amount = owned_materials.get(name, 0)
        required_amount = required_materials.get(name, 0)
        result[name] = max(owned_amount - required_amount, 0)

    return result


def calculate_required_abidos_powder(missing_materials: dict) -> dict:
    '''
    부족한 아비도스 목재를 가루 교환으로 채우기 위해
    필요한 가루 수량을 계산하여 반환
    '''
    missing_abidos_wood = missing_materials.get(ABIDOS_WOOD, 0)
    adjusted_abidos_wood  = round_up_to_unit(
        missing_abidos_wood,
        POWDER_TO_ABIDOS_RECIPE["획득재료"]
        )
    required_count = adjusted_abidos_wood  //  POWDER_TO_ABIDOS_RECIPE["획득재료"]
    required_powder = required_count * POWDER_TO_ABIDOS_RECIPE["필요재료"]

    return {
        "부족한 아비도스 목재" : missing_abidos_wood,
        "보정된 아비도스 목재" : adjusted_abidos_wood ,
        "교환필요횟수" : required_count,
        "필요한가루" : required_powder,
    }




def calculate_mixed_powder_exchange_plan(
    exchangeable_materials: dict,
    required_powder_info: dict,
    priority_order: list[str]
) -> dict:
    '''
    여러 재료를 우선순위에 따라 섞어서 가루 교환 계획을 만든다.
    '''
    original_required_powder = required_powder_info["필요한가루"]
    required_abidos_wood = required_powder_info["보정된 아비도스 목재"]

    remaining_required_powder = original_required_powder
    total_gained_powder = 0

    exchange_details = []
    used_materials = {}

    for material_name in priority_order:
        if remaining_required_powder <= 0:
            break

        recipe = EXCHANGE_RECIPES[material_name]
        material_amount = exchangeable_materials.get(material_name, 0)

        possible_exchange_count = (
            material_amount // recipe["필요재료"]
        )

        adjusted_powder = round_up_to_unit(
            remaining_required_powder,
            recipe["획득가루"]
        )

        required_exchange_count = (
            adjusted_powder // recipe["획득가루"]
        )

        exchange_count = min(
            possible_exchange_count,
            required_exchange_count
        )

        if exchange_count <= 0:
            continue

        used_amount = exchange_count * recipe["필요재료"]
        gained_powder = exchange_count * recipe["획득가루"]

        remaining_required_powder = max(
            remaining_required_powder - gained_powder,
            0
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
        // POWDER_TO_ABIDOS_RECIPE["필요재료"]
        * POWDER_TO_ABIDOS_RECIPE["획득재료"]
    )

    gained_abidos_wood = min(
        possible_abidos_wood,
        required_abidos_wood
    )

    return {
        "우선순위": priority_order,
        "필요가루": original_required_powder,
        "획득가루": total_gained_powder,
        "남은필요가루": remaining_required_powder,
        "필요아비도스목재": required_abidos_wood,
        "획득아비도스목재": gained_abidos_wood,
        "사용재료": used_materials,
        "교환상세": exchange_details,
        "가능여부": remaining_required_powder <= 0,
    }

def apply_abidos_exchange(
    owned_materials: dict,
    exchange_plan: dict
) -> dict:
    '''
    교환계획을 실제 보유재료에 반영하여 반환한다.
    '''
    after_exchange_materials = owned_materials.copy()

    for material_name, used_amount in exchange_plan["사용재료"].items():
        after_exchange_materials[material_name] = (
            after_exchange_materials.get(material_name, 0)
            - used_amount
        )

    after_exchange_materials[ABIDOS_WOOD] = (
        after_exchange_materials.get(ABIDOS_WOOD, 0)
        + exchange_plan["획득아비도스목재"]
    )

    return after_exchange_materials