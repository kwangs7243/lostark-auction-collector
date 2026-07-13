import unittest
from unittest.mock import call, patch

import src.abidos_calculator as ac
import src.market_prices as market_prices
import web_app
from src.constants import (
    ABIDOS_FUSION_MATERIAL,
    ABIDOS_WOOD,
    ADVANCED_ABIDOS_FUSION_MATERIAL,
    CATEGORY_CODES,
    RECIPES,
    SOFT_WOOD,
    STURDY_WOOD,
    WOOD,
)
from src.price_parser import extract_price_data


class PlanGenerationTest(unittest.TestCase):
    def test_exchange_then_purchase_can_reduce_purchase_cost(self):
        prices = {
            WOOD: 100,
            STURDY_WOOD: 100,
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
            STURDY_WOOD: 100,
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

    def test_generate_candidate_plans_uses_selected_recipe(self):
        prices = {
            WOOD: 100,
            STURDY_WOOD: 100,
            SOFT_WOOD: 300,
            ABIDOS_WOOD: 1000,
        }
        owned_materials = {
            WOOD: 0,
            SOFT_WOOD: 0,
            ABIDOS_WOOD: 0,
        }

        abidos_plans = ac.generate_candidate_plans(
            owned_materials,
            prices,
            craft_count=1,
            recipe=RECIPES["abidos"],
        )
        advanced_plans = ac.generate_candidate_plans(
            owned_materials,
            prices,
            craft_count=1,
            recipe=RECIPES["advanced_abidos"],
        )

        self.assertEqual(abidos_plans[0]["필요재료"][WOOD], 86)
        self.assertEqual(abidos_plans[0]["필요재료"][SOFT_WOOD], 45)
        self.assertEqual(abidos_plans[0]["필요재료"][ABIDOS_WOOD], 33)
        self.assertEqual(advanced_plans[0]["필요재료"][WOOD], 112)
        self.assertEqual(advanced_plans[0]["필요재료"][SOFT_WOOD], 59)
        self.assertEqual(advanced_plans[0]["필요재료"][ABIDOS_WOOD], 43)

    def test_calculation_prices_use_only_current_min_price(self):
        raw_prices = {
            WOOD: {
                "최저가": 100,
                "최근가": 120,
                "전일가": 9999,
            },
            SOFT_WOOD: {
                "최저가": 300,
                "최근가": 250,
                "전일가": 9999,
            },
            STURDY_WOOD: {
                "최저가": 150,
                "최근가": 140,
                "전일가": 9999,
            },
            ABIDOS_WOOD: {
                "최저가": 1000,
                "최근가": 900,
                "전일가": 9999,
            },
            ABIDOS_FUSION_MATERIAL: {
                "최저가": 50,
                "최근가": 48,
                "전일가": 9999,
            },
            ADVANCED_ABIDOS_FUSION_MATERIAL: {
                "최저가": 70,
                "최근가": 72,
                "전일가": 9999,
            },
        }

        prices = ac.build_calculation_prices(raw_prices)

        self.assertEqual(prices[WOOD], 100)
        self.assertEqual(prices[STURDY_WOOD], 150)
        self.assertEqual(prices[SOFT_WOOD], 300)
        self.assertEqual(prices[ABIDOS_WOOD], 1000)
        self.assertEqual(prices[ABIDOS_FUSION_MATERIAL], 50)
        self.assertEqual(prices[ADVANCED_ABIDOS_FUSION_MATERIAL], 70)

    def test_price_parser_does_not_require_recent_or_yesterday_price(self):
        prices = extract_price_data({
            "Items": [{
                "Name": WOOD,
                "CurrentMinPrice": 123,
            }]
        })

        self.assertEqual(prices, {WOOD: {"최저가": 123}})

    def test_required_price_validation_reports_missing_finished_product(self):
        with self.assertRaisesRegex(ValueError, ADVANCED_ABIDOS_FUSION_MATERIAL):
            ac.validate_required_prices({
                WOOD: 100,
                STURDY_WOOD: 100,
                SOFT_WOOD: 100,
                ABIDOS_WOOD: 100,
                ABIDOS_FUSION_MATERIAL: 100,
            })

    def test_price_parser_rejects_empty_market_items(self):
        with self.assertRaisesRegex(ValueError, "Items가 비어 있습니다"):
            extract_price_data({"Items": []})

    def test_wood_direct_purchase_rounds_up_to_hundred(self):
        prices = {
            WOOD: 100,
            STURDY_WOOD: 1000,
        }

        first_bundle = ac.build_wood_direct_purchase_candidate(prices, 100)
        second_bundle = ac.build_wood_direct_purchase_candidate(prices, 101)

        self.assertEqual(first_bundle["구매목재"], 100)
        self.assertEqual(first_bundle["비용"], 100)
        self.assertEqual(second_bundle["구매목재"], 200)
        self.assertEqual(second_bundle["비용"], 200)

    def test_sturdy_wood_exchange_uses_exchange_and_purchase_units(self):
        prices = {
            WOOD: 1000,
            STURDY_WOOD: 100,
        }

        candidate = ac.build_sturdy_wood_exchange_candidate(prices, 51)

        self.assertEqual(candidate["교환횟수"], 2)
        self.assertEqual(candidate["사용튼튼한목재"], 10)
        self.assertEqual(candidate["구매튼튼한목재"], 100)
        self.assertEqual(candidate["획득목재"], 100)
        self.assertEqual(candidate["남은목재"], 49)
        self.assertEqual(candidate["남은튼튼한목재"], 90)
        self.assertEqual(candidate["비용"], 100)

    def test_wood_fill_plan_selects_sturdy_wood_when_actual_cost_is_lower(self):
        prices = {
            WOOD: 500,
            STURDY_WOOD: 100,
        }

        plan = ac.build_wood_fill_purchase_plan(prices, 101)

        self.assertEqual(plan["선택방식"], "튼튼한 목재 구매 후 교환")
        self.assertEqual(plan["선택비용"], 100)
        self.assertEqual(plan["직접구매후보"]["구매목재"], 200)
        self.assertEqual(plan["튼튼한목재교환후보"]["교환횟수"], 3)
        self.assertEqual(plan["튼튼한목재교환후보"]["남은튼튼한목재"], 85)

    def test_wood_fill_plan_prefers_direct_purchase_when_costs_are_equal(self):
        prices = {
            WOOD: 100,
            STURDY_WOOD: 100,
        }

        plan = ac.build_wood_fill_purchase_plan(prices, 1)

        self.assertEqual(plan["선택방식"], "목재 직접 구매")

    def test_wood_fill_plan_does_not_create_mixed_purchase_for_large_shortage(self):
        prices = {
            WOOD: 100,
            STURDY_WOOD: 150,
        }

        plan = ac.build_wood_fill_purchase_plan(prices, 1001)

        self.assertEqual(
            plan["튼튼한목재교환후보"]["구매튼튼한목재"],
            200,
        )
        self.assertEqual(plan["튼튼한목재교환후보"]["교환횟수"], 21)
        self.assertNotIn(WOOD, plan["튼튼한목재교환후보"]["직접구매계획"])

    def test_smart_plan_applies_sturdy_wood_exchange_and_keeps_leftovers(self):
        prices = {
            WOOD: 500,
            STURDY_WOOD: 100,
            SOFT_WOOD: 300,
            ABIDOS_WOOD: 1000,
        }
        owned_materials = {
            WOOD: 0,
            SOFT_WOOD: 0,
            ABIDOS_WOOD: 0,
        }

        plan = ac.calculate_smart_purchase_plan(
            owned_materials,
            prices,
            craft_count=1,
            recipe={WOOD: 101},
        )

        self.assertTrue(plan["제작가능여부"])
        self.assertEqual(
            plan["구매계획"]["목재조달계획"]["선택방식"],
            "튼튼한 목재 구매 후 교환",
        )
        self.assertEqual(plan["구매비용"], 100)
        self.assertEqual(plan["제작후남은재료"][WOOD], 49)
        self.assertEqual(plan["제작후남은재료"][STURDY_WOOD], 85)

    def test_smart_plan_combines_craft_and_powder_exchange_wood(self):
        prices = {
            WOOD: 500,
            STURDY_WOOD: 100,
            SOFT_WOOD: 1000,
            ABIDOS_WOOD: 10000,
        }
        missing_materials = {
            WOOD: 112,
            SOFT_WOOD: 0,
            ABIDOS_WOOD: 43,
        }

        plan = ac.build_smart_purchase_plan(prices, missing_materials)
        wood_plan = plan["목재조달계획"]

        self.assertEqual(plan["구매방식"], "목재 구매 후 교환")
        self.assertEqual(wood_plan["부족목재"], 812)
        self.assertEqual(wood_plan["선택방식"], "튼튼한 목재 구매 후 교환")
        self.assertEqual(
            wood_plan["직접구매후보"]["구매목재"],
            900,
        )
        self.assertEqual(
            wood_plan["튼튼한목재교환후보"]["사용튼튼한목재"],
            85,
        )
        self.assertEqual(plan["총비용"], 100)
        self.assertNotIn(WOOD, plan["교환용구매계획"])

    def test_smart_plan_combines_soft_wood_before_bundle_rounding(self):
        prices = {
            WOOD: 1000,
            STURDY_WOOD: 10000,
            SOFT_WOOD: 100,
            ABIDOS_WOOD: 10000,
        }
        missing_materials = {
            WOOD: 0,
            SOFT_WOOD: 40,
            ABIDOS_WOOD: 20,
        }

        plan = ac.build_smart_purchase_plan(prices, missing_materials)
        soft_purchase = plan["교환용구매계획"][SOFT_WOOD]

        self.assertEqual(plan["구매방식"], "부드러운 목재 구매 후 교환")
        self.assertEqual(soft_purchase["부족한재료"], 190)
        self.assertEqual(soft_purchase["구매재료"], 200)
        self.assertEqual(soft_purchase["비용"], 200)
        self.assertEqual(plan["총비용"], 200)

    def test_exchange_comparison_uses_owned_surplus_before_purchase(self):
        prices = {
            WOOD: 118,
            STURDY_WOOD: 1184,
            SOFT_WOOD: 238,
            ABIDOS_WOOD: 1522,
        }
        owned_materials = {
            WOOD: 13000,
            SOFT_WOOD: 2360,
            ABIDOS_WOOD: 1045,
        }
        required_materials = ac.get_required_materials(
            40,
            RECIPES["advanced_abidos"],
        )
        best_plan = ac.select_best_plan(ac.generate_candidate_plans(
            owned_materials,
            prices,
            40,
            RECIPES["advanced_abidos"],
        ))

        comparison = web_app._build_exchange_material_comparison(
            prices,
            owned_materials,
            required_materials,
            best_plan,
        )
        wood_row = next(
            row for row in comparison["rows"]
            if row["material"] == WOOD
        )
        soft_wood_row = next(
            row for row in comparison["rows"]
            if row["material"] == SOFT_WOOD
        )

        self.assertEqual(wood_row["procurement_method"], "추가 조달 없음")
        self.assertEqual(wood_row["buy_material"], WOOD)
        self.assertEqual(wood_row["buy_amount"], 0)
        self.assertEqual(wood_row["total_candidate_cost"], 0)
        self.assertGreater(soft_wood_row["total_candidate_cost"], 0)

    @patch("src.market_prices.search_market_item")
    def test_market_prices_fetches_both_craft_products_by_exact_name(self, mock_search):
        def response_for(name: str, price: int) -> dict:
            return {
                "Items": [{
                    "Name": name,
                    "CurrentMinPrice": price,
                    "YDayAvgPrice": price,
                    "RecentPrice": price,
                }]
            }

        mock_search.side_effect = [
            response_for(WOOD, 100),
            response_for(ABIDOS_FUSION_MATERIAL, 50),
            response_for(ADVANCED_ABIDOS_FUSION_MATERIAL, 70),
        ]

        prices = market_prices.get_market_prices()

        self.assertIn(ABIDOS_FUSION_MATERIAL, prices)
        self.assertIn(ADVANCED_ABIDOS_FUSION_MATERIAL, prices)
        self.assertEqual(mock_search.call_args_list, [
            call(category_code=CATEGORY_CODES["벌목전리품"]),
            call(
                item_name=ABIDOS_FUSION_MATERIAL,
                category_code=CATEGORY_CODES["재련재료"],
            ),
            call(
                item_name=ADVANCED_ABIDOS_FUSION_MATERIAL,
                category_code=CATEGORY_CODES["재련재료"],
            ),
        ])

    def test_craft_market_comparison_uses_requested_craft_count(self):
        result = web_app._build_craft_market_comparison(
            "abidos",
            craft_count=2,
            best_plan={"구매비용": 100},
            prices={ABIDOS_FUSION_MATERIAL: 50},
        )

        self.assertEqual(result["product"]["total_output"], 20)
        self.assertEqual(result["product"]["total_craft_cost"], 664)
        self.assertEqual(result["craft_vs_market"]["craft_total_outlay"], 764)
        self.assertEqual(result["craft_vs_market"]["market_purchase_cost"], 1000)
        self.assertEqual(result["craft_vs_market"]["difference_buy_minus_craft"], 236)
        self.assertEqual(result["craft_vs_market"]["recommended_method"], "직접 제작")
        self.assertEqual(result["craft_vs_market"]["craft_unit_cost"], 38.2)

    def test_craft_market_comparison_buys_finished_product_per_item(self):
        result = web_app._build_craft_market_comparison(
            "advanced_abidos",
            craft_count=1,
            best_plan={"구매비용": 0},
            prices={ADVANCED_ABIDOS_FUSION_MATERIAL: 10},
        )

        self.assertEqual(result["product"]["total_craft_cost"], 431)
        self.assertEqual(result["craft_vs_market"]["market_purchase_quantity"], 10)
        self.assertEqual(result["craft_vs_market"]["market_purchase_cost"], 100)
        self.assertEqual(result["craft_vs_market"]["recommended_method"], "완제품 구매")

    def test_craft_market_comparison_handles_equal_cost_and_zero_count(self):
        equal_result = web_app._build_craft_market_comparison(
            "abidos",
            craft_count=1,
            best_plan={"구매비용": 8},
            prices={ABIDOS_FUSION_MATERIAL: 34},
        )
        zero_result = web_app._build_craft_market_comparison(
            "abidos",
            craft_count=0,
            best_plan={"구매비용": 0},
            prices={ABIDOS_FUSION_MATERIAL: 34},
        )

        self.assertEqual(equal_result["craft_vs_market"]["recommended_method"], "비용 동일")
        self.assertEqual(zero_result["product"]["total_output"], 0)
        self.assertEqual(zero_result["craft_vs_market"]["recommended_method"], "비교 대상 없음")
        self.assertIsNone(zero_result["craft_vs_market"]["craft_unit_cost"])

    @patch("web_app.get_market_prices")
    def test_web_post_renders_wood_procurement_comparison(self, mock_prices):
        mock_prices.return_value = {
            WOOD: {"최저가": 500, "최근가": 500, "전일가": 500},
            STURDY_WOOD: {"최저가": 100, "최근가": 100, "전일가": 100},
            SOFT_WOOD: {"최저가": 300, "최근가": 300, "전일가": 300},
            ABIDOS_WOOD: {"최저가": 1000, "최근가": 1000, "전일가": 1000},
            ABIDOS_FUSION_MATERIAL: {"최저가": 50, "최근가": 50, "전일가": 50},
            ADVANCED_ABIDOS_FUSION_MATERIAL: {"최저가": 70, "최근가": 70, "전일가": 70},
        }
        client = web_app.app.test_client()

        response = client.post("/", data={
            "recipe_key": "advanced_abidos",
            "craft_count": "1",
            "wood": "0",
            "soft_wood": "59",
            "abidos_wood": "43",
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("목재 조달 비교".encode(), response.data)
        self.assertIn("튼튼한 목재 구매 후 교환".encode(), response.data)
        self.assertIn("직접 제작 vs 완제품 구매".encode(), response.data)
        self.assertIn(ADVANCED_ABIDOS_FUSION_MATERIAL.encode(), response.data)
        self.assertIn("추천 제작 플랜".encode(), response.data)
        self.assertIn("최종 확보 방법".encode(), response.data)
        self.assertIn("가격 조회".encode(), response.data)
        self.assertIn("theme-toggle".encode(), response.data)
        self.assertIn("theme.js".encode(), response.data)
        self.assertIn("100개당".encode(), response.data)
        self.assertIn("개당".encode(), response.data)

    @patch("web_app.get_market_prices")
    def test_web_post_emphasizes_material_to_powder_exchange_count(self, mock_prices):
        mock_prices.return_value = {
            WOOD: {"최저가": 500, "최근가": 500, "전일가": 500},
            STURDY_WOOD: {"최저가": 100, "최근가": 100, "전일가": 100},
            SOFT_WOOD: {"최저가": 1000, "최근가": 1000, "전일가": 1000},
            ABIDOS_WOOD: {"최저가": 10000, "최근가": 10000, "전일가": 10000},
            ABIDOS_FUSION_MATERIAL: {"최저가": 50, "최근가": 50, "전일가": 50},
            ADVANCED_ABIDOS_FUSION_MATERIAL: {"최저가": 70, "최근가": 70, "전일가": 70},
        }
        client = web_app.app.test_client()

        response = client.post("/", data={
            "recipe_key": "advanced_abidos",
            "craft_count": "1",
            "wood": "0",
            "soft_wood": "59",
            "abidos_wood": "0",
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("목재 → 생활의 가루 7회 교환".encode(), response.data)
        self.assertIn("생활의 가루 → 아비도스 목재 5회 교환".encode(), response.data)
        self.assertIn("아비도스 교환 재료 비교".encode(), response.data)
        self.assertIn("교환 재료 가치".encode(), response.data)
        self.assertIn("실제 후보 총지출".encode(), response.data)

    @patch("web_app.get_market_prices")
    def test_web_calculation_uses_submitted_prices_without_api_lookup(self, mock_prices):
        client = web_app.app.test_client()
        data = {
            "recipe_key": "advanced_abidos",
            "craft_count": "1",
            "wood": "0",
            "soft_wood": "59",
            "abidos_wood": "43",
            "action": "calculate",
            "price_fetched_at": "2026-07-13 10:00:00",
        }
        submitted_prices = {
            "price_wood": 321,
            "price_sturdy_wood": 654,
            "price_soft_wood": 987,
            "price_abidos_wood": 1111,
            "price_abidos_fusion": 55,
            "price_advanced_abidos_fusion": 77,
        }
        for field_name, price in submitted_prices.items():
            data[field_name] = str(price)
            data[f"api_{field_name}"] = str(price - 1)

        response = client.post("/", data=data)

        self.assertEqual(response.status_code, 200)
        mock_prices.assert_not_called()
        self.assertIn('value="321"'.encode(), response.data)
        self.assertIn("직접 수정".encode(), response.data)
        self.assertIn("2026-07-13 10:00:00 조회".encode(), response.data)

    @patch("web_app.get_market_prices")
    def test_web_rejects_zero_submitted_price_without_api_lookup(self, mock_prices):
        client = web_app.app.test_client()
        data = {
            "recipe_key": "advanced_abidos",
            "craft_count": "1",
            "wood": "0",
            "soft_wood": "59",
            "abidos_wood": "43",
            "action": "calculate",
            "price_wood": "0",
            "price_sturdy_wood": "100",
            "price_soft_wood": "100",
            "price_abidos_wood": "100",
            "price_abidos_fusion": "100",
            "price_advanced_abidos_fusion": "100",
        }

        response = client.post("/", data=data)

        self.assertEqual(response.status_code, 200)
        mock_prices.assert_not_called()
        self.assertIn("목재 적용 가격은 1 이상이어야 합니다.".encode(), response.data)

    @patch("web_app.get_market_prices")
    def test_web_price_refresh_fetches_api_and_replaces_manual_prices(self, mock_prices):
        mock_prices.return_value = {
            WOOD: {"최저가": 101},
            STURDY_WOOD: {"최저가": 202},
            SOFT_WOOD: {"최저가": 303},
            ABIDOS_WOOD: {"최저가": 404},
            ABIDOS_FUSION_MATERIAL: {"최저가": 50},
            ADVANCED_ABIDOS_FUSION_MATERIAL: {"최저가": 70},
        }
        client = web_app.app.test_client()

        response = client.post("/", data={
            "recipe_key": "advanced_abidos",
            "craft_count": "1",
            "wood": "0",
            "soft_wood": "59",
            "abidos_wood": "43",
            "action": "refresh_prices",
            "price_wood": "9999",
        })

        self.assertEqual(response.status_code, 200)
        mock_prices.assert_called_once_with()
        self.assertIn('name="price_wood"'.encode(), response.data)
        self.assertIn('value="101"'.encode(), response.data)
        self.assertNotIn('value="9999"'.encode(), response.data)


if __name__ == "__main__":
    unittest.main()
