import math
from src.constants import (
    REQUIRED_PER_CRAFT, EXCHANGE_RECIPES, 
    POWDER, POWDER_TO_ABIDOS_RECIPE,
    WOOD, SOFT_WOOD, ABIDOS_WOOD)



def round_up_to_unit(amount: int, unit: int = 100) -> int:
    """
    수량을 unit 단위로 올림한다.
    예: 1 -> 100, 101 -> 200
    """
    return math.ceil(amount / unit) * unit


def build_calculation_prices(raw_prices:dict) ->dict:
    '''
    계산에 사용할 가격정보를 가공한다
    '''
    prices = {}
    for name,price_info in raw_prices.items():
        prices[name] = max(price_info["최저가"], price_info["최근가"])

    return prices

def get_required_materials(craft_count: int = 40) -> dict:
    '''
    제작에 필요한 재료의 총 갯수를 계산하여 반환
    '''
    return {
        name: amount * craft_count 
        for name, amount in REQUIRED_PER_CRAFT.items()
    }

def can_craft(owned_materials:dict, required_materials:dict) -> bool: # owned_materials: 보유재료 required_materials: 제작재료 
    '''
    제작필요갯수와 보유갯수를 비교하여 제작가능 여부를 반환
    '''
    for name, required_amount in required_materials.items():
        owned_amount = owned_materials.get(name, 0)
        if owned_amount < required_amount:
            return False
    return True
    
def get_missing_materials(owned_materials:dict, required_materials:dict) -> dict:
    '''
    제작에 부족한 재료와 재료의 갯수를 반환
    '''
    result = {}
    for name, required_amount in required_materials.items():
        owned_amount = owned_materials.get(name, 0)
        if owned_amount < required_amount:
            result[name] = required_amount - owned_amount
    return result


def calculate_missing_cost(prices:dict, missing_materials:dict) -> dict:
    '''
    제작에 부족한 재료의 구매 가격을 계산하여 반환
    '''
    result = {}
    for name, missing_amount in missing_materials.items():
        price = prices.get(name, 0)
        buy_amount = round_up_to_unit(missing_amount, 100)
        result[name] = {
            "부족한재료" : missing_amount,
            "구매재료" : buy_amount,
            "비용" : buy_amount * price // 100
        }
    return result

def calculate_remaining_materials(materials: dict, required_materials: dict) -> dict:
    """
    제작 후 남는 재료를 계산하여 반환
    """
    result = {}

    for name, owned_amount in materials.items():
        required_amount = required_materials.get(name, 0)
        result[name] = (
            owned_amount - required_amount 
            if owned_amount - required_amount > 0 else 0
            )

    return result

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
        "제작횟수" : craft_count,
        "플랜이름" : "부족재료 모두구매 후 제작",
        "구매전 제작가능여부": True,
        "필요재료": required_materials,
        "제작후 남은재료": after_craft_materials,
        "총비용": 0
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
        "제작횟수" : craft_count,
        "플랜이름" : "부족재료 모두구매 후 제작",
        "구매전 제작가능여부": False,
        "필요재료": required_materials,
        "부족한재료": missing_materials,
        "구매계획": purchase_plan,
        "구매후 재료": after_purchase_materials,
        "구매후 제작가능여부": True,
        "제작후 남은재료": after_craft_materials,
        "총비용": total_cost
    }

 
def calculate_required_abidos_powder(missing_materials: dict) -> dict:
    '''
    부족한 아비도스 목재를 가루 교환으로 채우기 위해
    필요한 가루 수량을 계산하여 반환
    '''
    missing_abidos_wood = missing_materials[ABIDOS_WOOD]
    adjusted_abidos_wood  = round_up_to_unit(
        missing_abidos_wood,
        POWDER_TO_ABIDOS_RECIPE["획득재료"]
        )
    exchange_count = adjusted_abidos_wood  //  POWDER_TO_ABIDOS_RECIPE["획득재료"]
    required_powder = exchange_count * POWDER_TO_ABIDOS_RECIPE["필요재료"]

    return {
        "부족한 아비도스 목재" : missing_abidos_wood,
        "보정된 아비도스 목재" : adjusted_abidos_wood ,
        "교환횟수" : exchange_count,
        "필요한가루" : required_powder,
        "총비용" : 0
    }

def calculate_powder_exchange_plans(
    owned_materials: dict,
    required_powder_info: dict,
) -> dict:
    '''
    보유재료를 각각 단독으로 사용했을 때
    필요한 가루를 만들 수 있는지 계산하여 반환한다.
    '''
    result = {}

    required_powder = required_powder_info["필요한가루"]
    gained_abidos_wood = required_powder_info["보정된 아비도스 목재"]

    for material_name, recipe in EXCHANGE_RECIPES.items():
        material_amount = owned_materials.get(material_name, 0)
        adjusted_powder = round_up_to_unit(
            required_powder,
            recipe["획득가루"]
        )
        exchange_count = adjusted_powder // recipe["획득가루"]
        used_amount = exchange_count * recipe["필요재료"]

        result[material_name] = {
            "재료이름": material_name,
            "필요한가루": required_powder,
            "보정된가루": adjusted_powder,
            "교환횟수": exchange_count,
            "필요한재료수량": used_amount,
            "보유재료수량": material_amount,
            "획득아비도스목재": gained_abidos_wood,
            "가능여부": material_amount >= used_amount,
        }

    return result

def apply_abidos_exchange(
    owned_materials: dict,
    exchange_plan: dict
) -> dict:
    '''
    선택된 교환계획을 보유재료에 반영하여 반환
    '''
    after_exchange_materials = owned_materials.copy()

    material_name = exchange_plan["재료이름"]
    used_amount = exchange_plan["필요한재료수량"]
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

def calculate_exchange_only_plan(
    owned_materials: dict,
    craft_count: int = 40
) -> dict:
    '''
    단일 재료 교환을 통한 제작 계획 반환
    '''
    required_materials = get_required_materials(craft_count)

    if can_craft(owned_materials, required_materials):
        after_craft_materials = calculate_remaining_materials(
            owned_materials,
            required_materials
        )

        return {
            "제작횟수": craft_count,
            "플랜이름": "단일재료 교환 제작",
            "교환전 제작가능여부": True,
            "필요재료": required_materials,
            "제작후 남은재료": after_craft_materials,
            "총비용": 0,
        }

    missing_materials = get_missing_materials(
        owned_materials,
        required_materials
    )

    required_powder_info = calculate_required_abidos_powder(
        missing_materials
    )

    exchange_plans = calculate_powder_exchange_plans(
        owned_materials,
        required_powder_info
    )

    selected_exchange_plan = None

    for plan in exchange_plans.values():
        if plan["가능여부"]:
            selected_exchange_plan = plan
            break

    after_exchange_materials = owned_materials.copy()

    if selected_exchange_plan is not None:
        after_exchange_materials = apply_abidos_exchange(
            owned_materials,
            selected_exchange_plan
        )

    can_craft_after_exchange = can_craft(
        after_exchange_materials,
        required_materials
    )

    after_craft_materials = None

    if can_craft_after_exchange:
        after_craft_materials = calculate_remaining_materials(
            after_exchange_materials,
            required_materials
        )

    return {
        "제작횟수": craft_count,
        "플랜이름": "단일재료 교환 제작",
        "교환전 제작가능여부": False,
        "필요재료": required_materials,
        "부족한재료": missing_materials,
        "필요가루정보": required_powder_info,
        "교환계획": exchange_plans,
        "선택된교환계획": selected_exchange_plan,
        "교환후 재료": after_exchange_materials,
        "교환후 제작가능여부": can_craft_after_exchange,
        "제작후 남은재료": after_craft_materials,
        "총비용": 0 if can_craft_after_exchange else None,
    }




