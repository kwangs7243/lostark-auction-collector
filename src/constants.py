WOOD = "목재"
STURDY_WOOD = "튼튼한 목재"
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

ABIDOS_FUSION_MATERIAL = "아비도스 융화 재료"
ADVANCED_ABIDOS_FUSION_MATERIAL = "상급 아비도스 융화 재료"

CRAFT_PRODUCTS = {
    "abidos": {
        "item_name": ABIDOS_FUSION_MATERIAL,
        "output_per_craft": 10,
        "craft_cost_per_craft": 332,
    },
    "advanced_abidos": {
        "item_name": ADVANCED_ABIDOS_FUSION_MATERIAL,
        "output_per_craft": 10,
        "craft_cost_per_craft": 431,
    },
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

STURDY_WOOD_TO_WOOD_RECIPE = {
    "required_sturdy_wood": 5,
    "gained_wood": 50,
}

CATEGORY_CODES = {
    "재련재료": 50010,
    "벌목전리품": 90300,
}

PRICE_INPUTS = {
    "price_wood": {
        "item_name": WOOD,
        "unit_label": "100개당",
    },
    "price_sturdy_wood": {
        "item_name": STURDY_WOOD,
        "unit_label": "100개당",
    },
    "price_soft_wood": {
        "item_name": SOFT_WOOD,
        "unit_label": "100개당",
    },
    "price_abidos_wood": {
        "item_name": ABIDOS_WOOD,
        "unit_label": "100개당",
    },
    "price_abidos_fusion": {
        "item_name": ABIDOS_FUSION_MATERIAL,
        "unit_label": "개당",
    },
    "price_advanced_abidos_fusion": {
        "item_name": ADVANCED_ABIDOS_FUSION_MATERIAL,
        "unit_label": "개당",
    },
}
