# Evaluation of the chosen model (out-of-time test set)

Model: **XGBoost**. Test: 155,296 loans, default rate 15.0%.

## Calibration: predicted vs actual default rate by score decile

|   XGBoost |   loans |   predicted_% |   actual_% |
|----------:|--------:|--------------:|-----------:|
|         1 | 15530.0 |           2.9 |        2.9 |
|         2 | 15530.0 |           5.1 |        5.3 |
|         3 | 15529.0 |           7.1 |        7.4 |
|         4 | 15530.0 |           8.9 |        9.6 |
|         5 | 15529.0 |          10.8 |       12.2 |
|         6 | 15530.0 |          12.8 |       14.4 |
|         7 | 15529.0 |          15.2 |       17.6 |
|         8 | 15530.0 |          18.2 |       20.6 |
|         9 | 15529.0 |          22.2 |       25.1 |
|        10 | 15530.0 |          30.3 |       34.9 |


Riskiest 10% of loans default 12.0x as often as the safest 10% (34.9% vs 2.9%).

## Approval policy: approve the lowest-risk loans, judged on what they actually paid

Realized return = total received / amount funded - 1, over each loan's life (not annualized).

|   approved_% |   default_rate_% (XGBoost) |   realized_return_% (XGBoost) |   default_rate_% (LC sub-grade) |   realized_return_% (LC sub-grade) |
|-------------:|---------------------------:|------------------------------:|--------------------------------:|-----------------------------------:|
|        50.00 |                       7.49 |                          7.19 |                            7.93 |                               6.80 |
|        55.00 |                       8.06 |                          7.16 |                            8.56 |                               6.79 |
|        60.00 |                       8.64 |                          7.13 |                            9.18 |                               6.73 |
|        65.00 |                       9.30 |                          7.03 |                            9.77 |                               6.66 |
|        70.00 |                       9.91 |                          6.97 |                           10.36 |                               6.64 |
|        75.00 |                      10.57 |                          6.89 |                           11.02 |                               6.56 |
|        80.00 |                      11.26 |                          6.79 |                           11.66 |                               6.49 |
|        85.00 |                      12.00 |                          6.64 |                           12.30 |                               6.39 |
|        90.00 |                      12.79 |                          6.45 |                           13.05 |                               6.23 |
|        95.00 |                      13.73 |                          6.18 |                           13.89 |                               6.04 |
|       100.00 |                      15.00 |                          5.70 |                           15.00 |                               5.70 |


## What drives the score (mean |SHAP|, 5,000 test loans)

|                       |   mean_abs_shap |
|:----------------------|----------------:|
| sub_grade             |          0.3508 |
| grade                 |          0.1258 |
| dti                   |          0.0973 |
| home_ownership        |          0.0960 |
| open_acc              |          0.0944 |
| annual_inc            |          0.0905 |
| addr_state            |          0.0870 |
| loan_to_income        |          0.0786 |
| inq_last_6mths        |          0.0625 |
| revol_util            |          0.0602 |
| revol_bal_to_income   |          0.0490 |
| emp_years             |          0.0458 |
| int_rate              |          0.0449 |
| credit_history_months |          0.0403 |
| revol_bal             |          0.0392 |

