def select_best_plan(candidate_plans: list[dict]) -> dict:
    """제작 가능한 플랜 중 구매비용이 가장 낮고, 동률이면 사용재료가치가 낮은 플랜을 고른다."""
    valid_plans = [
        plan for plan in candidate_plans
        if plan.get("제작가능여부")
    ]

    if not valid_plans:
        return {}

    return min(
        valid_plans,
        key=lambda plan: (
            plan.get("구매비용", plan.get("총비용", 0)),
            plan.get("사용재료가치", 0),
        ),
    )
