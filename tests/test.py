import unittest

import src.abidos_calculator as ac
from src.constants import ABIDOS_WOOD, SOFT_WOOD, WOOD


class PlanGenerationTest(unittest.TestCase):
    def test_exchange_then_purchase_can_reduce_purchase_cost(self):
        prices = {
            WOOD: 100,
            SOFT_WOOD: 300,
            ABIDOS_WOOD: 1000,
        }
        owned_materials = {
            WOOD: 11000,
            SOFT_WOOD: 1146,
            ABIDOS_WOOD: 13,
        }

        direct_plan = ac.calculate_direct_purchase_plan(
            owned_materials,
            prices,
            craft_count=40,
        )
        mixed_plan = ac.calculate_mixed_exchange_then_purchase_plan(
            owned_materials,
            prices,
            craft_count=40,
        )

        self.assertTrue(direct_plan["제작가능여부"])
        self.assertTrue(mixed_plan["제작가능여부"])
        self.assertLess(mixed_plan["구매비용"], direct_plan["구매비용"])
        self.assertGreater(mixed_plan["사용재료가치"], 0)

    def test_best_plan_prioritizes_purchase_cost_before_owned_material_value(self):
        candidate_plans = [
            {
                "플랜이름": "구매 없음, 재료 사용",
                "제작가능여부": True,
                "구매비용": 0,
                "사용재료가치": 10000,
            },
            {
                "플랜이름": "구매 있음, 재료 보존",
                "제작가능여부": True,
                "구매비용": 3000,
                "사용재료가치": 0,
            },
        ]

        best_plan = ac.select_best_plan(candidate_plans)

        self.assertEqual(best_plan["플랜이름"], "구매 없음, 재료 사용")

    def test_generate_candidate_plans_returns_valid_best_plan(self):
        prices = {
            WOOD: 100,
            SOFT_WOOD: 300,
            ABIDOS_WOOD: 1000,
        }
        owned_materials = {
            WOOD: 15555,
            SOFT_WOOD: 1500,
            ABIDOS_WOOD: 100,
        }

        plans = ac.generate_candidate_plans(
            owned_materials,
            prices,
            craft_count=40,
        )
        best_plan = ac.select_best_plan(plans)

        self.assertGreaterEqual(len(plans), 4)
        self.assertTrue(best_plan["제작가능여부"])
        self.assertIn("구매비용", best_plan)


if __name__ == "__main__":
    unittest.main()
