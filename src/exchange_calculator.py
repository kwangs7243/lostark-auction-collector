from src.constants import (
    EXCHANGE_RECIPES,
    POWDER_TO_ABIDOS_RECIPE,
    WOOD,
    SOFT_WOOD,
    ABIDOS_WOOD,
)
from src.material_utils import round_up_to_unit


def get_used_materials_from_exchange_plan(exchange_plan: dict) -> dict:
    '''
    교환에 들어가는 재료의 갯수를 반환
    '''
    material_name = exchange_plan["재료이름"]

    if exchange_plan["가능여부"]:
        used_amount = exchange_plan["필요재료수량"]
    else:
        used_amount = exchange_plan["잉여재료수량"]

    return {
        material_name: used_amount
    }


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


def calculate_powder_exchange_plans(
    exchangeable_materials: dict,
    required_powder_info: dict,
) -> dict:
    '''
    보유잉여재료를 각각 단독으로 사용했을 때
    필요한 가루를 만들 수 있는지 계산하여 반환한다.
    '''
    result = {}

    required_powder = required_powder_info["필요한가루"]
    required_abidos_wood = required_powder_info["보정된 아비도스 목재"]

    for material_name, recipe in EXCHANGE_RECIPES.items():
        material_amount = exchangeable_materials.get(material_name, 0)
        adjusted_powder = round_up_to_unit(
            required_powder,
            recipe["획득가루"]
        )
        required_count = adjusted_powder // recipe["획득가루"]
        required_amount = required_count * recipe["필요재료"]
        can_exchage = (
            False
            if required_powder == 0 
            else material_amount >= required_amount
            )
        can_exchage_count = material_amount // recipe["필요재료"]
        gained_powder = can_exchage_count * recipe["획득가루"]
        gained_abidos_wood = (
            gained_powder // POWDER_TO_ABIDOS_RECIPE["필요재료"] 
            * POWDER_TO_ABIDOS_RECIPE["획득재료"]
            )
        if material_amount >= required_amount:
            gained_powder = adjusted_powder
            gained_abidos_wood = required_abidos_wood

        result[material_name] = {
            "재료이름": material_name,
            "필요재료수량": required_amount,
            "잉여재료수량": material_amount,
            "필요교환횟수": required_count,
            "가능교환횟수":can_exchage_count,
            "필요한가루": adjusted_powder,
            "획득가루": gained_powder,
            "필요아비도스목재": required_abidos_wood,
            "획득아비도스목재": gained_abidos_wood,
            "가능여부": can_exchage
        }

    return result


def calculate_mixed_powder_exchange_plan(
    exchangeable_materials: dict,
    required_powder: int,
    priority_order: list[str]
) -> dict:
    '''
    여러 재료를 우선순위에 따라 섞어서 가루 교환 계획을 만든다.
    '''
    exchange_details = []
    used_materials = {}

    for material_name in priority_order:
        if required_powder <= 0:
            break

        recipe = EXCHANGE_RECIPES[material_name]
        material_amount = exchangeable_materials.get(material_name, 0)

        possible_exchange_count = (
            material_amount // recipe["필요재료"]
        )

        adjusted_powder = round_up_to_unit(
            required_powder,
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

        required_powder = max(
            required_powder - gained_powder,
            0
        )

        used_materials[material_name] = (
            used_materials.get(material_name, 0)
            + used_amount
        )

        exchange_details.append({
            "재료이름": material_name,
            "교환횟수": exchange_count,
            "사용재료수량": used_amount,
            "획득가루": gained_powder,
            "교환후남은필요가루": required_powder,
        })

    gained_powder = required_powder - required_powder

    gained_abidos_wood = (
        gained_powder
        // POWDER_TO_ABIDOS_RECIPE["필요재료"]
        * POWDER_TO_ABIDOS_RECIPE["획득재료"]
    )

    return {
        "우선순위": priority_order,
        "필요가루": required_powder,
        "획득가루": gained_powder,
        "남은필요가루": required_powder,
        "획득아비도스목재": gained_abidos_wood,
        "사용재료": used_materials,
        "교환상세": exchange_details,
        "가능여부": required_powder <= 0,
    }


def apply_abidos_exchange(
    owned_materials: dict,
    exchange_plan: dict
) -> dict:
    '''
    선택된 교환계획 1개를 실제 보유재료에 반영하여 반환
    '''
    after_exchange_materials = owned_materials.copy()

    material_name = exchange_plan["재료이름"]

    if exchange_plan["가능여부"]:
        used_amount = exchange_plan["필요재료수량"]
        gained_abidos_wood = exchange_plan["필요아비도스목재"]
    else:
        used_amount = exchange_plan["잉여재료수량"]
        gained_abidos_wood = exchange_plan["획득아비도스목재"]

    after_exchange_materials[material_name] = (
        after_exchange_materials.get(material_name, 0)
        - used_amount
    )

    after_exchange_materials[ABIDOS_WOOD] = (
        after_exchange_materials.get(ABIDOS_WOOD, 0)
        + gained_abidos_wood
    )

    return after_exchange_materials
