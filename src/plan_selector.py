def select_best_plan(candidate_plans: list[dict]) -> dict:
    '''
    제작 가능한 후보 중 가장 좋은 플랜을 선택한다.
    '''
    valid_plans = [
        plan for plan in candidate_plans
        if plan.get("제작가능여부")
    ]

    if not valid_plans:
        return {}

    return min(
        valid_plans,
        key=lambda plan: (
            plan.get("총비용", 0),
            plan.get("사용재료가치", 0),
        )
    )
