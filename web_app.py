from flask import Flask, render_template, request

import src.abidos_calculator as ac
from src.constants import (
    ABIDOS_WOOD,
    DEFAULT_RECIPE_KEY,
    RECIPE_LABELS,
    RECIPES,
    SOFT_WOOD,
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


def _calculate(form_data: dict) -> dict:
    owned_materials = {
        WOOD: form_data["wood"],
        SOFT_WOOD: form_data["soft_wood"],
        ABIDOS_WOOD: form_data["abidos_wood"],
    }
    recipe = RECIPES[form_data["recipe_key"]]
    raw_prices = get_market_prices()
    prices = ac.build_calculation_prices(raw_prices)
    candidate_plans = ac.generate_candidate_plans(
        owned_materials=owned_materials,
        prices=prices,
        craft_count=form_data["craft_count"],
        recipe=recipe,
    )

    return {
        "recipe_label": RECIPE_LABELS[form_data["recipe_key"]],
        "owned_materials": owned_materials,
        "prices": prices,
        "candidate_plans": candidate_plans,
        "best_plan": ac.select_best_plan(candidate_plans),
    }


@app.route("/", methods=["GET", "POST"])
def index():
    form_data = DEFAULT_FORM.copy()
    result = None
    error = None

    if request.method == "POST":
        try:
            form_data = _build_form_data(request.form)
            result = _calculate(form_data)
        except Exception as exc:
            error = str(exc)

    return render_template(
        "index.html",
        error=error,
        form_data=form_data,
        recipe_labels=RECIPE_LABELS,
        result=result,
    )


def run() -> None:
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)


if __name__ == "__main__":
    run()
