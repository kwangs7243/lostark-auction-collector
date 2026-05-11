import math

from src.constants import REQUIRED_PER_CRAFT


def round_up_to_unit(amount: int, unit: int = 100) -> int:
    """
    수량을 unit 단위로 올림한다.
    예: 1 -> 100, 101 -> 200
    """
    return math.ceil(amount / unit) * unit


def get_required_materials(craft_count: int = 40) -> dict:
    '''
    제작에 필요한 재료의 총 갯수를 계산하여 반환
    '''
    return {
        name: amount * craft_count 
        for name, amount in REQUIRED_PER_CRAFT.items()
    }


def can_craft(owned_materials:dict, required_materials:dict) -> bool: 
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


def calculate_remaining_materials(
        owned_materials: dict, 
        required_materials: dict
        ) -> dict:
    """
    제작 후 남는 재료를 계산하여 반환
    """
    result = {}

    for name, owned_amount in owned_materials.items():
        required_amount = required_materials.get(name, 0)
        result[name] = max(owned_amount - required_amount, 0)

    return result


def calculate_material_value(materials: dict, prices: dict) -> int:
    '''
    재료들의 가격을 계산하여 반환
    '''
    total = 0

    for name, amount in materials.items():
        price = prices.get(name, 0)
        total += amount * price // 100

    return total
