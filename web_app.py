from datetime import datetime

from flask import Flask, render_template, request

import src.abidos_calculator as ac
from src.constants import (
    ABIDOS_WOOD,
    CRAFT_PRODUCTS,
    DEFAULT_RECIPE_KEY,
    PRICE_INPUTS,
    RECIPE_LABELS,
    RECIPES,
    SOFT_WOOD,
    STURDY_WOOD,
    WOOD,
)
from src.market_prices import get_market_prices

app = Flask(__name__)

DEFAULT_FORM = {
    "recipe_key": DEFAULT_RECIPE_KEY,
    "craft_count": 40,
    "wood": 27551,
    "soft_wood": 3818,
    "abidos_wood": 1045,
}


def _parse_positive_int(value: str, field_name: str) -> int:
    number = _parse_non_negative_int(value, field_name)
    if number <= 0:
        raise ValueError(f"{field_name}은 1 이상이어야 합니다.")
    return number


def _build_price_state(
    api_prices: dict,
    applied_prices: dict | None = None,
    fetched_at: str = "",
) -> dict:
    applied_prices = applied_prices or api_prices
    return {
        "api_prices": api_prices,
        "applied_prices": applied_prices,
        "fetched_at": fetched_at,
    }


def _fetch_price_state() -> dict:
    raw_prices = get_market_prices()
    api_prices = ac.build_calculation_prices(raw_prices)
    return _build_price_state(
        api_prices,
        fetched_at=datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
    )


def _parse_price_state(form) -> dict:
    applied_prices = {}
    api_prices = {}

    for field_name, config in PRICE_INPUTS.items():
        item_name = config["item_name"]
        applied_price = _parse_positive_int(
            form.get(field_name),
            f"{item_name} 적용 가격",
        )
        api_price = _parse_positive_int(
            form.get(f"api_{field_name}", applied_price),
            f"{item_name} API 최저가",
        )
        applied_prices[item_name] = applied_price
        api_prices[item_name] = api_price

    ac.validate_required_prices(applied_prices)
    return _build_price_state(
        api_prices,
        applied_prices,
        form.get("price_fetched_at", "사용자 입력"),
    )


def _summarize_price_inputs(price_state: dict | None) -> list[dict]:
    price_state = price_state or _build_price_state({}, {})
    api_prices = price_state["api_prices"]
    applied_prices = price_state["applied_prices"]

    return [
        {
            "field_name": field_name,
            "api_field_name": f"api_{field_name}",
            "item_name": config["item_name"],
            "unit_label": config["unit_label"],
            "api_price": api_prices.get(config["item_name"], ""),
            "applied_price": applied_prices.get(config["item_name"], ""),
            "is_modified": (
                config["item_name"] in api_prices
                and config["item_name"] in applied_prices
                and api_prices[config["item_name"]]
                != applied_prices[config["item_name"]]
            ),
        }
        for field_name, config in PRICE_INPUTS.items()
    ]


def _summarize_purchase_plan(purchase_plan: dict) -> list[dict]:
    items = []

    for group_name, label in [
        ("직접구매계획", "직접 구매"),
        ("교환용구매계획", "교환용 구매"),
    ]:
        for material_name, plan in purchase_plan.get(group_name, {}).items():
            items.append({
                "label": label,
                "material": material_name,
                "missing_amount": plan.get("부족한재료", 0),
                "buy_amount": plan.get("구매재료", 0),
                "cost": plan.get("비용", 0),
            })

    return items


def _summarize_exchange_plan(exchange_plan: dict | None) -> dict:
    if not exchange_plan:
        return {
            "has_exchange": False,
            "rows": [],
            "abidos_exchange_count": 0,
            "gained_abidos": 0,
            "used_materials": {},
        }

    return {
        "has_exchange": bool(exchange_plan.get("교환상세")),
        "rows": [
            {
                "material": detail.get("재료이름"),
                "exchange_count": detail.get("교환횟수", 0),
                "used_amount": detail.get("사용재료수량", 0),
                "gained_powder": detail.get("획득가루", 0),
            }
            for detail in exchange_plan.get("교환상세", [])
        ],
        "abidos_exchange_count": exchange_plan.get("아비도스목재교환횟수", 0),
        "gained_abidos": exchange_plan.get("획득아비도스목재", 0),
        "used_materials": exchange_plan.get("사용재료", {}),
    }


def _summarize_wood_procurement(wood_plan: dict) -> dict:
    direct = wood_plan["직접구매후보"]
    sturdy = wood_plan["튼튼한목재교환후보"]
    selected_method = wood_plan["선택방식"]

    return {
        "has_shortage": wood_plan["부족목재"] > 0,
        "missing_wood": wood_plan["부족목재"],
        "selected_method": selected_method,
        "selected_cost": wood_plan["선택비용"],
        "rows": [
            {
                "is_selected": selected_method == direct["방식"],
                "method": direct["방식"],
                "buy_material": WOOD,
                "buy_amount": direct["구매목재"],
                "exchange_count": 0,
                "gained_wood": direct["구매목재"],
                "remaining_wood": direct["남은목재"],
                "remaining_sturdy_wood": 0,
                "cost": direct["비용"],
            },
            {
                "is_selected": selected_method == sturdy["방식"],
                "method": sturdy["방식"],
                "buy_material": STURDY_WOOD,
                "buy_amount": sturdy["구매튼튼한목재"],
                "exchange_count": sturdy["교환횟수"],
                "gained_wood": sturdy["획득목재"],
                "remaining_wood": sturdy["남은목재"],
                "remaining_sturdy_wood": sturdy["남은튼튼한목재"],
                "cost": sturdy["비용"],
            },
        ],
    }


def _build_exchange_material_comparison(
    prices: dict,
    owned_materials: dict,
    required_materials: dict,
    best_plan: dict,
) -> dict:
    """목재와 부드러운 목재를 각각 전량 사용하는 교환 후보를 비교한다."""
    missing_materials = ac.get_missing_materials(
        owned_materials,
        required_materials,
    )
    missing_abidos_wood = missing_materials.get(ABIDOS_WOOD, 0)
    if missing_abidos_wood <= 0:
        return {
            "has_shortage": False,
            "missing_abidos_wood": 0,
            "rows": [],
        }

    selected_materials = set(
        (best_plan.get("교환계획") or {}).get("사용재료", {})
    )
    rows = []

    for candidate in ac.build_abidos_fill_purchase_candidates(
        prices,
        missing_abidos_wood,
    ):
        exchange_plan = candidate.get("구매후교환계획")
        if not exchange_plan or not exchange_plan.get("교환상세"):
            continue

        detail = exchange_plan["교환상세"][0]
        material_name = detail["재료이름"]
        if material_name not in [WOOD, SOFT_WOOD]:
            continue

        used_amount = detail["사용재료수량"]
        combined_missing_materials = {
            name: amount
            for name, amount in missing_materials.items()
            if name != ABIDOS_WOOD and amount > 0
        }
        combined_material_shortage = max(
            required_materials.get(material_name, 0)
            + used_amount
            - owned_materials.get(material_name, 0),
            0,
        )
        if combined_material_shortage > 0:
            combined_missing_materials[material_name] = combined_material_shortage
        else:
            combined_missing_materials.pop(material_name, None)

        wood_plan = ac.build_wood_fill_purchase_plan(
            prices,
            combined_missing_materials.pop(WOOD, 0),
        )
        normal_purchase_plan = ac.calculate_missing_cost(
            prices,
            combined_missing_materials,
        )
        total_candidate_cost = (
            wood_plan["총비용"]
            + ac.calculate_purchase_cost(normal_purchase_plan)
        )

        procurement_method = f"{material_name} 직접 구매"
        buy_material = material_name
        buy_amount = 0
        procurement_cost = 0

        if material_name == WOOD:
            procurement_method = wood_plan["선택방식"]
            procurement_cost = wood_plan["선택비용"]
            if procurement_method == "목재 직접 구매":
                buy_amount = wood_plan["직접구매후보"]["구매목재"]
            elif procurement_method == "튼튼한 목재 구매 후 교환":
                buy_material = STURDY_WOOD
                buy_amount = wood_plan["튼튼한목재교환후보"]["구매튼튼한목재"]
        else:
            purchase = normal_purchase_plan.get(material_name, {})
            buy_amount = purchase.get("구매재료", 0)
            procurement_cost = purchase.get("비용", 0)
            if not purchase:
                procurement_method = f"보유 {material_name} 사용"

        rows.append({
            "material": material_name,
            "exchange_count": detail["교환횟수"],
            "used_amount": used_amount,
            "gained_powder": detail["획득가루"],
            "remaining_powder": max(
                detail["획득가루"] - exchange_plan["필요가루"],
                0,
            ),
            "material_value": ac.calculate_material_value(
                {material_name: used_amount},
                prices,
            ),
            "procurement_method": procurement_method,
            "buy_material": buy_material,
            "buy_amount": buy_amount,
            "procurement_cost": procurement_cost,
            "total_candidate_cost": total_candidate_cost,
            "used_in_best": material_name in selected_materials,
        })

    lowest_cost = min(
        (row["total_candidate_cost"] for row in rows),
        default=0,
    )
    for row in rows:
        row["is_lowest_cost"] = row["total_candidate_cost"] == lowest_cost

    rows.sort(key=lambda row: row["material"] != WOOD)
    return {
        "has_shortage": True,
        "missing_abidos_wood": missing_abidos_wood,
        "rows": rows,
    }


def _summarize_plan(plan: dict, is_best: bool = False) -> dict:
    purchase_items = _summarize_purchase_plan(plan.get("구매계획", {}))
    exchange_summary = _summarize_exchange_plan(plan.get("교환계획"))

    return {
        "name": plan.get("플랜이름", ""),
        "is_best": is_best,
        "can_craft": plan.get("제작가능여부", False),
        "purchase_cost": plan.get("구매비용", 0),
        "exchange_material_value": plan.get("사용재료가치", 0),
        "required_materials": plan.get("필요재료", {}),
        "missing_materials": plan.get("부족한재료", {}),
        "remaining_materials": plan.get("제작후남은재료") or {},
        "purchase_items": purchase_items,
        "exchange": exchange_summary,
    }


def _build_craft_market_comparison(
    recipe_key: str,
    craft_count: int,
    best_plan: dict,
    prices: dict,
) -> dict:
    """선택 제품의 직접 제작 실제 지출과 동일 수량 완제품 구매비를 비교한다."""
    product_config = CRAFT_PRODUCTS[recipe_key]
    item_name = product_config["item_name"]
    output_per_craft = product_config["output_per_craft"]
    craft_cost_per_craft = product_config["craft_cost_per_craft"]
    total_output = craft_count * output_per_craft
    total_craft_cost = craft_count * craft_cost_per_craft
    material_procurement_cost = best_plan.get("구매비용", 0)
    craft_total_outlay = material_procurement_cost + total_craft_cost
    market_unit_price = prices[item_name]
    market_purchase_cost = total_output * market_unit_price
    difference = market_purchase_cost - craft_total_outlay

    if total_output <= 0:
        recommended_method = "비교 대상 없음"
        recommendation_tone = "neutral"
        recommendation_title = "비교할 제작 수량이 없습니다"
        recommendation_description = "제작 횟수를 입력하면 두 확보 방법을 비교합니다."
        craft_unit_cost = None
    elif difference > 0:
        recommended_method = "직접 제작"
        recommendation_tone = "craft"
        recommendation_title = "직접 제작이 더 유리해요"
        recommendation_description = f"완제품 구매보다 {difference:,}골드 적게 지출합니다."
        craft_unit_cost = craft_total_outlay / total_output
    elif difference < 0:
        recommended_method = "완제품 구매"
        recommendation_tone = "market"
        recommendation_title = "완제품 구매가 더 유리해요"
        recommendation_description = f"직접 제작보다 {abs(difference):,}골드 적게 지출합니다."
        craft_unit_cost = craft_total_outlay / total_output
    else:
        recommended_method = "비용 동일"
        recommendation_tone = "neutral"
        recommendation_title = "두 방법의 비용이 같아요"
        recommendation_description = "선호하는 확보 방법을 선택하면 됩니다."
        craft_unit_cost = craft_total_outlay / total_output

    return {
        "product": {
            "item_name": item_name,
            "craft_count": craft_count,
            "output_per_craft": output_per_craft,
            "total_output": total_output,
            "craft_cost_per_craft": craft_cost_per_craft,
            "total_craft_cost": total_craft_cost,
            "market_unit_price": market_unit_price,
        },
        "craft_vs_market": {
            "material_procurement_cost": material_procurement_cost,
            "total_craft_cost": total_craft_cost,
            "craft_total_outlay": craft_total_outlay,
            "market_purchase_quantity": total_output,
            "market_purchase_cost": market_purchase_cost,
            "difference_buy_minus_craft": difference,
            "recommended_method": recommended_method,
            "recommendation_tone": recommendation_tone,
            "recommendation_title": recommendation_title,
            "recommendation_description": recommendation_description,
            "savings_amount": abs(difference),
            "craft_unit_cost": craft_unit_cost,
            "market_unit_price": market_unit_price,
        },
    }


def _parse_non_negative_int(value: str, field_name: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name}은 숫자로 입력해야 합니다.") from exc

    if number < 0:
        raise ValueError(f"{field_name}은 0 이상이어야 합니다.")

    return number


def _build_form_data(form) -> dict:
    recipe_key = form.get("recipe_key", DEFAULT_FORM["recipe_key"])
    if recipe_key not in RECIPES:
        raise ValueError("알 수 없는 레시피입니다.")

    return {
        "recipe_key": recipe_key,
        "craft_count": _parse_non_negative_int(
            form.get("craft_count", DEFAULT_FORM["craft_count"]),
            "제작 횟수",
        ),
        "wood": _parse_non_negative_int(
            form.get("wood", DEFAULT_FORM["wood"]),
            "보유 목재",
        ),
        "soft_wood": _parse_non_negative_int(
            form.get("soft_wood", DEFAULT_FORM["soft_wood"]),
            "보유 부드러운 목재",
        ),
        "abidos_wood": _parse_non_negative_int(
            form.get("abidos_wood", DEFAULT_FORM["abidos_wood"]),
            "보유 아비도스 목재",
        ),
    }


def _calculate(
    form_data: dict,
    prices: dict,
    price_fetched_at: str,
) -> dict:
    owned_materials = {
        WOOD: form_data["wood"],
        SOFT_WOOD: form_data["soft_wood"],
        ABIDOS_WOOD: form_data["abidos_wood"],
    }
    recipe = RECIPES[form_data["recipe_key"]]
    ac.validate_required_prices(prices)
    required_materials = ac.get_required_materials(
        form_data["craft_count"],
        recipe,
    )
    candidate_plans = ac.generate_candidate_plans(
        owned_materials=owned_materials,
        prices=prices,
        craft_count=form_data["craft_count"],
        recipe=recipe,
    )
    best_plan = ac.select_best_plan(candidate_plans)
    wood_procurement = best_plan.get("구매계획", {}).get("목재조달계획")
    if wood_procurement is None:
        missing_wood = max(
            required_materials.get(WOOD, 0) - owned_materials.get(WOOD, 0),
            0,
        )
        wood_procurement = ac.build_wood_fill_purchase_plan(prices, missing_wood)
    craft_market_comparison = _build_craft_market_comparison(
        form_data["recipe_key"],
        form_data["craft_count"],
        best_plan,
        prices,
    )
    exchange_material_comparison = _build_exchange_material_comparison(
        prices,
        owned_materials,
        required_materials,
        best_plan,
    )

    return {
        "recipe_label": RECIPE_LABELS[form_data["recipe_key"]],
        "owned_materials": owned_materials,
        "prices": prices,
        "price_fetched_at": price_fetched_at,
        "wood_procurement": _summarize_wood_procurement(wood_procurement),
        "exchange_material_comparison": exchange_material_comparison,
        **craft_market_comparison,
        "candidate_plans": candidate_plans,
        "best_plan": best_plan,
        "candidate_summaries": [
            _summarize_plan(
                plan,
                is_best=plan == best_plan,
            )
            for plan in candidate_plans
        ],
        "best_summary": _summarize_plan(best_plan, is_best=True) if best_plan else None,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    form_data = DEFAULT_FORM.copy()
    result = None
    error = None
    price_state = None

    if request.method == "GET":
        try:
            price_state = _fetch_price_state()
        except Exception as exc:
            error = str(exc)
    else:
        try:
            form_data = _build_form_data(request.form)
            action = request.form.get("action", "calculate")
            has_submitted_prices = all(
                field_name in request.form
                for field_name in PRICE_INPUTS
            )
            if action == "refresh_prices" or not has_submitted_prices:
                price_state = _fetch_price_state()
            else:
                price_state = _parse_price_state(request.form)

            result = _calculate(
                form_data,
                price_state["applied_prices"],
                price_state["fetched_at"],
            )
        except Exception as exc:
            error = str(exc)

    return render_template(
        "index.html",
        error=error,
        form_data=form_data,
        recipe_labels=RECIPE_LABELS,
        price_rows=_summarize_price_inputs(price_state),
        price_fetched_at=(price_state or {}).get("fetched_at", ""),
        result=result,
    )


def run() -> None:
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)


if __name__ == "__main__":
    run()
