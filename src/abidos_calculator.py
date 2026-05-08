REQUIRED_PER_CRAFT = {
    "목재": 112,
    "부드러운 목재": 59,
    "아비도스 목재": 43,
}

def build_calculation_prices(raw_prices:dict) ->dict:
    '''
    계산에 사용할 가격정보를 가공한다
    '''
    prices = {}
    for name,price_info in raw_prices.items():
        prices[name] = max(price_info["min_price"], price_info["recent_price"])

    return prices

def get_required_materials(craft_count: int = 40) -> dict:
    '''
    제작에 필요한 재료의 총 갯수를 계산
    '''
    return {
        name: amount * craft_count 
        for name, amount in REQUIRED_PER_CRAFT.items()
    }

