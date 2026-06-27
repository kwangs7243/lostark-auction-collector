WOOD = "목재"
SOFT_WOOD = "부드러운 목재"
ABIDOS_WOOD = "아비도스 목재"
POWDER = "생활의 가루"

PURCHASE_UNIT = 100

ABIDOS_PER_CRAFT = {
    WOOD: 86,
    SOFT_WOOD: 45,
    ABIDOS_WOOD: 33,
}
ADVANCED_ABIDOS_PER_CRAFT = {
    WOOD: 112,
    SOFT_WOOD: 59,
    ABIDOS_WOOD: 43,
}

RECIPES = {
    "abidos": ABIDOS_PER_CRAFT,
    "advanced_abidos": ADVANCED_ABIDOS_PER_CRAFT,
}

RECIPE_LABELS = {
    "abidos": "아비도스",
    "advanced_abidos": "상급 아비도스",
}

DEFAULT_RECIPE_KEY = "advanced_abidos"

EXCHANGE_RECIPES = {
    WOOD: {
        "required_material": 100,
        "gained_powder": 80,
    },
    SOFT_WOOD: {
        "required_material": 50,
        "gained_powder": 80,
    },
}

POWDER_TO_ABIDOS_RECIPE = {
    "required_powder": 100,
    "gained_abidos": 10,
}

CATEGORY_CODES = {
    "재련재료": 50010,
    "벌목전리품": 90300,
}
