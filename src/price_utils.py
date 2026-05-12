from src.constants import EXCHANGE_RECIPES
from src.material_utils import round_up_to_unit

# 제작 책임없는
# 순수 가격계산
def build_calculation_prices(raw_prices:dict) ->dict:
    '''
    계산에 사용할 가격정보를 가공한다
    '''
    prices = {}
    for name,price_info in raw_prices.items():
        prices[name] = max(price_info["최저가"], price_info["최근가"])

    return prices


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


def calculate_powder_unit_cost(
    material_name: str,
    lumber_prices: dict
) -> float:
    '''
    특정 재료로 가루 1개를 만들 때의 실제 거래소 기준 비용을 계산한다.
    거래소 가격은 100개 묶음 기준이다.
    '''
    recipe = EXCHANGE_RECIPES[material_name]

    bundle_price = lumber_prices[material_name]

    return (
        bundle_price
        / 100
        * recipe["필요재료"]
        / recipe["획득가루"]
    )


def get_priority_order(prices: dict) -> list[str]:
    '''
    가루 1개당 비용이 낮은 재료 순서로 정렬한다.
    '''
    return sorted(
        EXCHANGE_RECIPES,
        key=lambda material_name: calculate_powder_unit_cost(
            material_name,
            prices
        )
    )
