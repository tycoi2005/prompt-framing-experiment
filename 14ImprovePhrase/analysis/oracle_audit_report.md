# Independent Task Specification & Test-Oracle Audit (`R1C6` & `R2C12`)

## 1. Python Code Benchmarks Summary (100 Tasks, 700 Assertions)

| dataset | n_tasks | ref_pass_n | clean_n | zero_param_n | const_return_n | dup_test_tasks | exact_float_eq_tasks | sig_missing_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| API Code (MathNet) | 50 | 50 | 50 | 0 | 0 | 0 | 0 | 0 |
| Local Code (TOANMATH) | 50 | 50 | 0 | 3 | 1 | 0 | 16 | 50 |

## 2. Flagged Python Tasks (Edge Cases, Float Equality, Zero-Param, or Signature Issues)

| dataset | task_id | difficulty | func_name | n_params | flags |
| --- | --- | --- | --- | --- | --- |
| Local Code (TOANMATH) | 1 | hard | calculate_max_reward | 3 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 2 | medium | calculate_max_lantern_volume | 1 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 3 | hard | calculate_probability | 6 | EXACT_FLOAT_EQ(7); FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 4 | medium | calculate_paved_area | 3 | EXACT_FLOAT_EQ(7); FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 5 | easy | solve_tsp | 1 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 6 | hard | solve_stacks | 2 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 7 | hard | maximize_oil_production | 3 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 8 | easy | max_revenue | 8 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 9 | medium | calculate_crab_area | 1 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 10 | medium | calculate_tuning_angle | 3 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 11 | easy | calculate_max_slope | 2 | EXACT_FLOAT_EQ(7); FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 12 | hard | solve_octagon_prob | 1 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 13 | medium | solve_probability_inverse | 0 | ZERO_PARAM; FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 14 | hard | solve_production | 8 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 15 | medium | solve_min_products | 3 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 16 | easy | total_pages_written | 2 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 17 | medium | calculate_months_to_deplete | 3 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 18 | medium | max_charity_revenue | 8 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 19 | hard | maximize_revenue | 4 | EXACT_FLOAT_EQ(7); FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 20 | hard | solve_shortest_path | 1 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 21 | medium | count_ap_triplets | 2 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 22 | hard | min_travel_time | 4 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 23 | medium | calculate_win_probability | 1 | EXACT_FLOAT_EQ(7); FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 24 | hard | calculate_geese_survival | 4 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 25 | hard | min_distance_lizards | 7 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 26 | medium | count_grid_ways | 1 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 27 | easy | calculate_grouped_std | 2 | EXACT_FLOAT_EQ(7); FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 28 | hard | maximize_profit | 6 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 29 | hard | solve_silk_profit | 9 | EXACT_FLOAT_EQ(6); FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 30 | medium | max_profit | 8 | EXACT_FLOAT_EQ(7); FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 31 | hard | count_rotor_arrangements | 2 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 32 | hard | solve_min_distance | 2 | EXACT_FLOAT_EQ(7); FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 33 | hard | solve_min_cost_days | 4 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 34 | hard | solve_max_profit | 9 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 35 | hard | solve_overflow | 3 | EXACT_FLOAT_EQ(6); FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 36 | hard | solve_grid_probability | 0 | ZERO_PARAM; FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 37 | hard | solve_polygon_triangle_color | 1 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 38 | hard | maximize_profit_price | 5 | EXACT_FLOAT_EQ(7); FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 39 | easy | solve_max_profit | 8 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 40 | medium | calculate_flight_angle | 2 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 41 | medium | calculate_savings | 3 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 42 | easy | calculate_probability_score | 5 | EXACT_FLOAT_EQ(7); FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 43 | hard | calculate_dark_area | 1 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 44 | hard | solve_gps_problem | 4 | EXACT_FLOAT_EQ(7); FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 45 | easy | solve_mlu_probability | 4 | EXACT_FLOAT_EQ(7); FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 46 | medium | solve_lantern_problem | 0 | ZERO_PARAM; CONST_RETURN; EXACT_FLOAT_EQ(7); FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 47 | hard | solve_bookshelf | 2 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 48 | easy | calculate_probability | 2 | EXACT_FLOAT_EQ(7); FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 49 | hard | calculate_glue_cost | 3 | FUNC_NAME_NOT_IN_TEXT |
| Local Code (TOANMATH) | 50 | hard | find_min_first_payment | 4 | FUNC_NAME_NOT_IN_TEXT |

## 3. Math Benchmarks Summary (100 Tasks)

| dataset | n_tasks | parse_ok_n | clean_n | n_int | n_frac | n_dec |
| --- | --- | --- | --- | --- | --- | --- |
| API Math (MathNet) | 50 | 50 | 50 | 44 | 6 | 0 |
| Local Math (VietJack) | 50 | 50 | 49 | 27 | 22 | 1 |

## 4. Flagged Math Tasks

| dataset | task_id | difficulty | expected_answer | flags |
| --- | --- | --- | --- | --- |
| Local Math (VietJack) | 48 | hard | 961.6 | DECIMAL_NO_ROUNDING_NOTE |
