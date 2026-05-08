# 재료명
WOOD = "목재"
SOFT_WOOD = "부드러운 목재"
ABIDOS_WOOD = "아비도스 목재"
POWDER = "생활의 가루"

# 제작 필요 재료
REQUIRED_PER_CRAFT = {
    WOOD: 112,
    SOFT_WOOD: 59,
    ABIDOS_WOOD: 43,
}

# 교환 비율

EXCHANGE_RECIPES = {
    WOOD: {
        "필요갯수": 100,
        "획득갯수": 80,
    },

    SOFT_WOOD: {
        "필요갯수": 50,
        "획득갯수": 80,
    }
}

POWDER_TO_ABIDOS_RECIPE = {
    "필요갯수": 100,
    "획득갯수": 10,
}

# 로스트아크 API 카테고리 코드
CATEGORY_CODES = {
    "재련재료": 50010,
    "벌목전리품": 90300,
}