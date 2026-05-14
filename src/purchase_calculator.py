from src.constants import (
    ABIDOS_WOOD,
    EXCHANGE_RECIPES,
    POWDER_TO_ABIDOS_RECIPE,
)
from src.exchange_calculator import calculate_required_abidos_powder
from src.material_utils import round_up_to_unit
from src.price_utils import compare_abidos_purchase_vs_exchange


# 구매 계획 계산
# 가격 판단 결과를 바탕으로 직접 구매 / 교환용 재료 구매 계획을 만든다.


def calculate_missing_cost(
    prices: dict,
    missing_materials: dict
) -> dict:
    '''
    부족한 재료를 거래소에서 직접 구매할 때의 구매 계획을 반환한다.
    거래소 가격은 100개 묶음 기준이다.
    '''
    result = {}

    for name, missing_amount in missing_materials.items():
        if missing_amount <= 0:
            continue

        price = prices[name]
        buy_amount = round_up_to_unit(missing_amount, 100)

        result[name] = {
            "부족한재료": missing_amount,
            "구매재료": buy_amount,
            "비용": buy_amount * price // 100,
        }

    return result


def calculate_purchase_cost(purchase_plan: dict) -> int:
    '''
    구매계획의 총 구매비용을 계산한다.
    '''
    return sum(
        item["비용"]
        for item in purchase_plan.values()
    )


def apply_purchase_plan(
    owned_materials: dict,
    purchase_plan: dict
) -> dict:
    '''
    구매계획을 보유재료에 반영하여 반환한다.
    '''
    after_purchase_materials = owned_materials.copy()

    for name, plan in purchase_plan.items():
        after_purchase_materials[name] = (
            after_purchase_materials.get(name, 0)
            + plan["구매재료"]
        )

    return after_purchase_materials


def _build_abidos_exchange_purchase_plan(
    prices: dict,
    missing_abidos_wood: int,
    price_compare: dict
) -> dict:
    '''
    부족한 아비도스 목재를 교환으로 얻기 위한
    교환용 재료 구매계획과 교환계획을 만든다.
    '''
    required_powder_info = calculate_required_abidos_powder({
        ABIDOS_WOOD: missing_abidos_wood
    })

    material_name = price_compare["가루최저재료"]
    recipe = EXCHANGE_RECIPES[material_name]

    required_powder = required_powder_info["필요한가루"]

    adjusted_powder = round_up_to_unit(
        required_powder,
        recipe["획득가루"]
    )
    exchange_count = adjusted_powder // recipe["획득가루"]

    used_amount = exchange_count * recipe["필요재료"]
    buy_amount = round_up_to_unit(used_amount, 100)
    gained_powder = exchange_count * recipe["획득가루"]

    possible_abidos_wood = (
        gained_powder
        // POWDER_TO_ABIDOS_RECIPE["필요재료"]
        * POWDER_TO_ABIDOS_RECIPE["획득재료"]
    )

    gained_abidos_wood = min(
        possible_abidos_wood,
        required_powder_info["보정된 아비도스 목재"]
    )

    abidos_exchange_count = (
        gained_abidos_wood
        // POWDER_TO_ABIDOS_RECIPE["획득재료"]
    )

    exchange_purchase_plan = {
        material_name: {
            "부족한재료": used_amount,
            "구매재료": buy_amount,
            "비용": buy_amount * prices[material_name] // 100,
        }
    }

    exchange_plan = {
        "우선순위": price_compare["우선순위"],
        "필요가루": required_powder,
        "획득가루": gained_powder,
        "남은필요가루": max(required_powder - gained_powder, 0),
        "아비도스목재교환횟수": abidos_exchange_count,
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
        "필요가루정보": required_powder_info,
        "교환용구매계획": exchange_purchase_plan,
        "구매후교환계획": exchange_plan,
    }


def build_smart_purchase_plan(
    prices: dict,
    missing_materials: dict
) -> dict:
    '''
    부족재료를 채우기 위한 구매계획을 만든다.

    아비도스 목재는 직접 구매와 교환용 재료 구매 중
    거래소 가격 기준으로 더 싼 방식을 선택한다.
    나머지 부족재료는 직접 구매한다.
    '''
    price_compare = compare_abidos_purchase_vs_exchange(prices)

    missing_abidos_wood = missing_materials.get(ABIDOS_WOOD, 0)
    normal_missing_materials = {
        name: amount
        for name, amount in missing_materials.items()
        if name != ABIDOS_WOOD and amount > 0
    }

    direct_purchase_plan = calculate_missing_cost(
        prices,
        normal_missing_materials
    )

    exchange_purchase_plan = {}
    exchange_plan = None
    required_powder_info = {}
    selected_method = "직접구매"

    if missing_abidos_wood > 0:
        if price_compare["직접구매추천"]:
            abidos_purchase_plan = calculate_missing_cost(
                prices,
                {ABIDOS_WOOD: missing_abidos_wood}
            )
            direct_purchase_plan.update(abidos_purchase_plan)
        else:
            selected_method = "교환구매"
            exchange_result = _build_abidos_exchange_purchase_plan(
                prices,
                missing_abidos_wood,
                price_compare
            )
            required_powder_info = exchange_result["필요가루정보"]
            exchange_purchase_plan = exchange_result["교환용구매계획"]
            exchange_plan = exchange_result["구매후교환계획"]

    direct_purchase_cost = calculate_purchase_cost(direct_purchase_plan)
    exchange_purchase_cost = calculate_purchase_cost(exchange_purchase_plan)
    total_cost = direct_purchase_cost + exchange_purchase_cost

    return {
        "구매방식": selected_method,
        "가격비교": price_compare,
        "직접구매계획": direct_purchase_plan,
        "교환용구매계획": exchange_purchase_plan,
        "필요가루정보": required_powder_info,
        "구매후교환계획": exchange_plan,
        "직접구매비용": direct_purchase_cost,
        "교환용구매비용": exchange_purchase_cost,
        "총비용": total_cost,
    }


def apply_smart_purchase_plan(
    owned_materials: dict,
    smart_purchase_plan: dict
) -> dict:
    '''
    스마트 구매계획을 보유재료에 반영한다.

    1. 직접구매 재료 추가
    2. 교환용 구매 재료 추가
    3. 구매 후 교환계획이 있으면 교환 반영
    '''
    after_purchase_materials = owned_materials.copy()

    after_purchase_materials = apply_purchase_plan(
        after_purchase_materials,
        smart_purchase_plan.get("직접구매계획", {})
    )

    after_purchase_materials = apply_purchase_plan(
        after_purchase_materials,
        smart_purchase_plan.get("교환용구매계획", {})
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
