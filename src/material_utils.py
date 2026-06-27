import math

from src.constants import PURCHASE_UNIT


def round_up_to_unit(amount: int | float, unit: int = PURCHASE_UNIT) -> int:
    """수량을 지정한 거래 단위로 올림 처리한다."""
    if amount <= 0:
        return 0
    return math.ceil(amount / unit) * unit


def get_required_materials(craft_count: int, recipe: dict) -> dict:
    """제작 횟수에 필요한 전체 재료 수량을 계산한다."""
    return {
        name: amount * craft_count
        for name, amount in recipe.items()
    }


def can_craft(owned_materials: dict, required_materials: dict) -> bool:
    """보유 재료만으로 필요한 재료를 모두 충족하는지 확인한다."""
    return all(
        owned_materials.get(name, 0) >= required_amount
        for name, required_amount in required_materials.items()
    )


def get_missing_materials(owned_materials: dict, required_materials: dict) -> dict:
    """제작에 부족한 재료와 부족 수량만 골라 반환한다."""
    return {
        name: required_amount - owned_materials.get(name, 0)
        for name, required_amount in required_materials.items()
        if owned_materials.get(name, 0) < required_amount
    }


def calculate_remaining_materials(
    owned_materials: dict,
    required_materials: dict,
) -> dict:
    """필요 재료를 사용한 뒤 남는 보유 재료 수량을 계산한다."""
    result = {}

    for name, owned_amount in owned_materials.items():
        required_amount = required_materials.get(name, 0)
        result[name] = max(owned_amount - required_amount, 0)

    return result


def calculate_material_value(materials: dict, prices: dict) -> int:
    """재료 수량을 현재 계산 가격 기준의 골드 가치로 환산한다."""
    total = 0

    for name, amount in materials.items():
        if amount <= 0:
            continue
        total += amount * prices[name] // PURCHASE_UNIT

    return total
