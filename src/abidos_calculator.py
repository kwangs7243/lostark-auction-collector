import math
from src.constants import (REQUIRED_PER_CRAFT, CATEGORY_CODES, EXCHANGE_RECIPES, POWDER,)



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
    제작 후 남는 재료를 계산한다.
    """
    result = {}

    for name, owned_amount in materials.items():
        required_amount = required_materials.get(name, 0)
        result[name] = owned_amount - required_amount

    return result

def calculate_direct_purchase_plan(owned_materials: dict, prices: dict, craft_count: int = 40) -> dict:
    """
    직접 구매만 하여 제작 가능한 계획을 반환한다.
    """
    required_materials = get_required_materials(craft_count)
    missing_materials = get_missing_materials(owned_materials, required_materials)
    purchase_plan = calculate_missing_cost(prices, missing_materials)

    total_cost = sum(item["비용"] for item in purchase_plan.values())

    after_purchase_materials = owned_materials.copy()

    for name, plan in purchase_plan.items():
        after_purchase_materials[name] = (
            after_purchase_materials.get(name, 0)
            + plan["구매재료"]
        )
    after_craft_materials = calculate_remaining_materials(after_purchase_materials, required_materials)

    return {
        "제작횟수": craft_count,
        "구매전 제작가능여부": can_craft(owned_materials, required_materials),
        "필요재료": required_materials,
        "부족한재료": missing_materials,
        "구매계획": purchase_plan,
        "구매후 재료": after_purchase_materials,
        "구매후 제작가능여부": can_craft(after_purchase_materials, required_materials),
        "제작후 남은재료": after_craft_materials,
        "총구매비용": total_cost
    }

def calculate_exchangeable_powder(materials: dict) -> dict:
    """
    보유 재료로 교환 가능한 가루 수량을 계산한다.
    """
    result = {}
    total_powder = 0

    for material_name, recipe in EXCHANGE_RECIPES.items():

        owned_material = materials.get(material_name, 0)

        required_amount = recipe["필요갯수"]
        powder_amount = recipe["획득갯수"]

        exchange_count = owned_material // required_amount

        used_material = exchange_count * required_amount

        gained_powder = exchange_count * powder_amount

        remaining_material = owned_material - used_material

        result[material_name] = {
            "교환횟수": exchange_count,
            "사용재료": used_material,
            "획득가루": gained_powder,
            "남은재료": remaining_material,
        }

        total_powder += gained_powder

    result[POWDER] = total_powder

    return result