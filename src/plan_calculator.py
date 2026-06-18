from src.exchange_calculator import (
    apply_abidos_exchange,
    calculate_exchangeable_materials,
    calculate_mixed_powder_exchange_plan,
    calculate_required_abidos_powder,
)
from src.constants import ABIDOS_WOOD
from src.material_utils import (
    calculate_material_value,
    calculate_remaining_materials,
    can_craft,
    get_missing_materials,
    get_required_materials,
)
from src.price_utils import get_priority_order
from src.purchase_calculator import (
    apply_purchase_plan,
    apply_smart_purchase_plan,
    build_abidos_fill_purchase_candidates,
    build_smart_purchase_plan,
    calculate_missing_cost,
    calculate_purchase_cost,
)


def _build_plan_result(
    plan_name: str,
    craft_count: int,
    owned_materials: dict,
    required_materials: dict,
    exchange_plan: dict | None,
    after_exchange_materials: dict | None,
    purchase_plan: dict,
    after_purchase_materials: dict,
    used_materials: dict,
    prices: dict,
    purchase_cost: int,
    extra: dict | None = None,
) -> dict:
    """각 플랜 함수가 공통으로 사용하는 결과 dict를 만든다."""
    can_craft_result = can_craft(after_purchase_materials, required_materials)
    after_craft_materials = (
        calculate_remaining_materials(after_purchase_materials, required_materials)
        if can_craft_result
        else None
    )

    result = {
        "제작횟수": craft_count,
        "플랜이름": plan_name,
        "필요재료": required_materials,
        "부족한재료": get_missing_materials(owned_materials, required_materials),
        "교환계획": exchange_plan,
        "교환후재료": after_exchange_materials,
        "교환후부족재료": (
            get_missing_materials(after_exchange_materials, required_materials)
            if after_exchange_materials is not None
            else {}
        ),
        "구매계획": purchase_plan,
        "구매후재료": after_purchase_materials,
        "제작가능여부": can_craft_result,
        "제작후남은재료": after_craft_materials,
        "사용재료": used_materials,
        "사용재료가치": calculate_material_value(used_materials, prices),
        "구매비용": purchase_cost,
        # 현재 프로젝트에서 총비용은 선택 기준 1순위인 추가 구매 골드와 같은 의미다.
        "총비용": purchase_cost,
    }

    if extra:
        result.update(extra)

    return result


def _build_owned_only_result(
    owned_materials: dict,
    required_materials: dict,
    craft_count: int,
    prices: dict,
    plan_name: str = "보유재료만으로 제작",
) -> dict:
    """추가 구매나 교환 없이 보유 재료만으로 제작 가능한 플랜을 만든다."""
    return _build_plan_result(
        plan_name=plan_name,
        craft_count=craft_count,
        owned_materials=owned_materials,
        required_materials=required_materials,
        exchange_plan=None,
        after_exchange_materials=owned_materials.copy(),
        purchase_plan={},
        after_purchase_materials=owned_materials.copy(),
        used_materials={},
        prices=prices,
        purchase_cost=0,
    )


def calculate_direct_purchase_plan(
    owned_materials: dict,
    prices: dict,
    craft_count: int = 40,
) -> dict:
    """부족한 재료를 모두 직접 구매하는 기본 플랜을 만든다."""
    required_materials = get_required_materials(craft_count)

    if can_craft(owned_materials, required_materials):
        return _build_owned_only_result(
            owned_materials,
            required_materials,
            craft_count,
            prices,
        )

    missing_materials = get_missing_materials(
        owned_materials,
        required_materials,
    )
    purchase_plan = calculate_missing_cost(prices, missing_materials)
    after_purchase_materials = apply_purchase_plan(
        owned_materials,
        purchase_plan,
    )

    return _build_plan_result(
        plan_name="부족재료 직접 구매 후 제작",
        craft_count=craft_count,
        owned_materials=owned_materials,
        required_materials=required_materials,
        exchange_plan=None,
        after_exchange_materials=owned_materials.copy(),
        purchase_plan={
            "구매방식": "직접구매",
            "직접구매계획": purchase_plan,
            "총비용": calculate_purchase_cost(purchase_plan),
        },
        after_purchase_materials=after_purchase_materials,
        used_materials={},
        prices=prices,
        purchase_cost=calculate_purchase_cost(purchase_plan),
    )


def calculate_smart_purchase_plan(
    owned_materials: dict,
    prices: dict,
    craft_count: int = 40,
) -> dict:
    """부족 재료 중 아비도스 목재는 가장 싼 충당 방식을 골라 구매 플랜을 만든다."""
    required_materials = get_required_materials(craft_count)

    if can_craft(owned_materials, required_materials):
        return _build_owned_only_result(
            owned_materials,
            required_materials,
            craft_count,
            prices,
            "보유재료만으로 제작",
        )

    missing_materials = get_missing_materials(
        owned_materials,
        required_materials,
    )
    purchase_plan = build_smart_purchase_plan(prices, missing_materials)
    after_purchase_materials = apply_smart_purchase_plan(
        owned_materials,
        purchase_plan,
    )

    return _build_plan_result(
        plan_name="부족재료 스마트 구매 후 제작",
        craft_count=craft_count,
        owned_materials=owned_materials,
        required_materials=required_materials,
        exchange_plan=purchase_plan.get("구매후교환계획"),
        after_exchange_materials=None,
        purchase_plan=purchase_plan,
        after_purchase_materials=after_purchase_materials,
        used_materials={},
        prices=prices,
        purchase_cost=purchase_plan["총비용"],
    )


def calculate_mixed_exchange_only_plan(
    owned_materials: dict,
    prices: dict,
    craft_count: int = 40,
) -> dict:
    """보유 잉여 재료만 교환해서 제작 가능한지 확인하는 플랜을 만든다."""
    required_materials = get_required_materials(craft_count)

    if can_craft(owned_materials, required_materials):
        return _build_owned_only_result(
            owned_materials,
            required_materials,
            craft_count,
            prices,
        )

    missing_materials = get_missing_materials(
        owned_materials,
        required_materials,
    )
    required_powder_info = calculate_required_abidos_powder(missing_materials)
    exchangeable_materials = calculate_exchangeable_materials(
        owned_materials,
        required_materials,
    )
    exchange_plan = calculate_mixed_powder_exchange_plan(
        exchangeable_materials,
        required_powder_info,
        get_priority_order(prices),
    )
    after_exchange_materials = apply_abidos_exchange(
        owned_materials,
        exchange_plan,
    )
    used_materials = exchange_plan["사용재료"]

    return _build_plan_result(
        plan_name="보유 잉여재료 혼합교환 제작",
        craft_count=craft_count,
        owned_materials=owned_materials,
        required_materials=required_materials,
        exchange_plan=exchange_plan,
        after_exchange_materials=after_exchange_materials,
        purchase_plan={},
        after_purchase_materials=after_exchange_materials,
        used_materials=used_materials,
        prices=prices,
        purchase_cost=0,
        extra={
            "필요가루정보": required_powder_info,
            "교환가능재료": exchangeable_materials,
        },
    )


def calculate_mixed_exchange_then_purchase_plan(
    owned_materials: dict,
    prices: dict,
    craft_count: int = 40,
) -> dict:
    """보유 잉여 재료를 먼저 교환하고 남은 부족분을 구매하는 플랜을 만든다."""
    required_materials = get_required_materials(craft_count)

    if can_craft(owned_materials, required_materials):
        return _build_owned_only_result(
            owned_materials,
            required_materials,
            craft_count,
            prices,
        )

    missing_materials = get_missing_materials(
        owned_materials,
        required_materials,
    )
    required_powder_info = calculate_required_abidos_powder(missing_materials)
    exchangeable_materials = calculate_exchangeable_materials(
        owned_materials,
        required_materials,
    )
    exchange_plan = calculate_mixed_powder_exchange_plan(
        exchangeable_materials,
        required_powder_info,
        get_priority_order(prices),
    )
    after_exchange_materials = apply_abidos_exchange(
        owned_materials,
        exchange_plan,
    )
    after_exchange_missing = get_missing_materials(
        after_exchange_materials,
        required_materials,
    )
    purchase_plan = build_smart_purchase_plan(
        prices,
        after_exchange_missing,
    )
    after_purchase_materials = apply_smart_purchase_plan(
        after_exchange_materials,
        purchase_plan,
    )
    used_materials = exchange_plan["사용재료"]

    return _build_plan_result(
        plan_name="보유 잉여재료 혼합교환 후 스마트 구매",
        craft_count=craft_count,
        owned_materials=owned_materials,
        required_materials=required_materials,
        exchange_plan=exchange_plan,
        after_exchange_materials=after_exchange_materials,
        purchase_plan=purchase_plan,
        after_purchase_materials=after_purchase_materials,
        used_materials=used_materials,
        prices=prices,
        purchase_cost=purchase_plan["총비용"],
        extra={
            "필요가루정보": required_powder_info,
            "교환가능재료": exchangeable_materials,
        },
    )


def calculate_abidos_purchase_candidate_plans(
    owned_materials: dict,
    prices: dict,
    craft_count: int = 40,
) -> list[dict]:
    """아비도스 목재 부족분을 채우는 구매 후보들을 각각 제작 플랜으로 만든다."""
    required_materials = get_required_materials(craft_count)
    missing_materials = get_missing_materials(
        owned_materials,
        required_materials,
    )
    normal_missing_materials = {
        name: amount
        for name, amount in missing_materials.items()
        if name != ABIDOS_WOOD
    }
    normal_purchase_plan = calculate_missing_cost(
        prices,
        normal_missing_materials,
    )
    normal_after_purchase = apply_purchase_plan(
        owned_materials,
        normal_purchase_plan,
    )
    normal_purchase_cost = calculate_purchase_cost(normal_purchase_plan)
    abidos_candidates = build_abidos_fill_purchase_candidates(
        prices,
        missing_materials.get(ABIDOS_WOOD, 0),
    )

    plans = []
    for candidate in abidos_candidates:
        purchase_plan = {
            "구매방식": candidate["구매방식"],
            "직접구매계획": {
                **normal_purchase_plan,
                **candidate["직접구매계획"],
            },
            "교환용구매계획": candidate["교환용구매계획"],
            "필요가루정보": candidate["필요가루정보"],
            "구매후교환계획": candidate["구매후교환계획"],
            "총비용": normal_purchase_cost + candidate["총비용"],
        }
        after_purchase_materials = apply_smart_purchase_plan(
            normal_after_purchase,
            {
                "직접구매계획": candidate["직접구매계획"],
                "교환용구매계획": candidate["교환용구매계획"],
                "구매후교환계획": candidate["구매후교환계획"],
            },
        )

        plans.append(_build_plan_result(
            plan_name=f"아비도스 충당 후보 - {candidate['구매방식']}",
            craft_count=craft_count,
            owned_materials=owned_materials,
            required_materials=required_materials,
            exchange_plan=candidate["구매후교환계획"],
            after_exchange_materials=None,
            purchase_plan=purchase_plan,
            after_purchase_materials=after_purchase_materials,
            used_materials={},
            prices=prices,
            purchase_cost=purchase_plan["총비용"],
        ))

    return plans


def generate_candidate_plans(
    owned_materials: dict,
    prices: dict,
    craft_count: int = 40,
) -> list[dict]:
    """현재 보유 재료와 가격으로 비교할 전체 후보 플랜 목록을 생성한다."""
    plans = [
        calculate_direct_purchase_plan(owned_materials, prices, craft_count),
        calculate_smart_purchase_plan(owned_materials, prices, craft_count),
        calculate_mixed_exchange_only_plan(owned_materials, prices, craft_count),
        calculate_mixed_exchange_then_purchase_plan(owned_materials, prices, craft_count),
    ]
    plans.extend(
        calculate_abidos_purchase_candidate_plans(
            owned_materials,
            prices,
            craft_count,
        )
    )

    unique_plans = {}
    for plan in plans:
        key = (
            plan["플랜이름"],
            plan["구매비용"],
            plan["사용재료가치"],
        )
        unique_plans[key] = plan

    return list(unique_plans.values())
