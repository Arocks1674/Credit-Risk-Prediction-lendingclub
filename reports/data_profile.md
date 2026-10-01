# loan.csv profile

Rows: 2,260,668  |  Columns: 145

issue_d range: Jun 2007 to Dec 2018  |  latest last_pymnt_d (data snapshot): Feb 2019

## Loans issued per year

|   issue_d |   loans |
|----------:|--------:|
|      2007 |     603 |
|      2008 |    2393 |
|      2009 |    5281 |
|      2010 |   12537 |
|      2011 |   21721 |
|      2012 |   53367 |
|      2013 |  134814 |
|      2014 |  235629 |
|      2015 |  421095 |
|      2016 |  434407 |
|      2017 |  443579 |
|      2018 |  495242 |


## loan_status

| loan_status                                         |   loans |
|:----------------------------------------------------|--------:|
| Fully Paid                                          | 1041952 |
| Current                                             |  919695 |
| Charged Off                                         |  261655 |
| Late (31-120 days)                                  |   21897 |
| In Grace Period                                     |    8952 |
| Late (16-30 days)                                   |    3737 |
| Does not meet the credit policy. Status:Fully Paid  |    1988 |
| Does not meet the credit policy. Status:Charged Off |     761 |
| Default                                             |      31 |


## term x loan_status

| loan_status                                         |    36 months |    60 months |
|:----------------------------------------------------|-------------:|-------------:|
| Charged Off                                         |       159149 |       102506 |
| Current                                             |       598341 |       321354 |
| Default                                             |           20 |           11 |
| Does not meet the credit policy. Status:Charged Off |          649 |          112 |
| Does not meet the credit policy. Status:Fully Paid  |         1789 |          199 |
| Fully Paid                                          |       829605 |       212347 |
| In Grace Period                                     |         5119 |         3833 |
| Late (16-30 days)                                   |         2228 |         1509 |
| Late (31-120 days)                                  |        12854 |         9043 |


## Columns

|                                            | dtype   |   missing_% |
|:-------------------------------------------|:--------|------------:|
| id                                         | float64 |      100    |
| member_id                                  | float64 |      100    |
| loan_amnt                                  | int64   |        0    |
| funded_amnt                                | int64   |        0    |
| funded_amnt_inv                            | float64 |        0    |
| term                                       | str     |        0    |
| int_rate                                   | float64 |        0    |
| installment                                | float64 |        0    |
| grade                                      | str     |        0    |
| sub_grade                                  | str     |        0    |
| emp_title                                  | str     |        7.39 |
| emp_length                                 | str     |        6.5  |
| home_ownership                             | str     |        0    |
| annual_inc                                 | float64 |        0    |
| verification_status                        | str     |        0    |
| issue_d                                    | str     |        0    |
| loan_status                                | str     |        0    |
| pymnt_plan                                 | str     |        0    |
| url                                        | float64 |      100    |
| desc                                       | float64 |       94.42 |
| purpose                                    | str     |        0    |
| title                                      | str     |        1.03 |
| zip_code                                   | str     |        0    |
| addr_state                                 | str     |        0    |
| dti                                        | float64 |        0.08 |
| delinq_2yrs                                | int64   |        0    |
| earliest_cr_line                           | str     |        0    |
| inq_last_6mths                             | int64   |        0    |
| mths_since_last_delinq                     | float64 |       51.25 |
| mths_since_last_record                     | float64 |       84.11 |
| open_acc                                   | int64   |        0    |
| pub_rec                                    | int64   |        0    |
| revol_bal                                  | int64   |        0    |
| revol_util                                 | float64 |        0.08 |
| total_acc                                  | int64   |        0    |
| initial_list_status                        | str     |        0    |
| out_prncp                                  | float64 |        0    |
| out_prncp_inv                              | float64 |        0    |
| total_pymnt                                | float64 |        0    |
| total_pymnt_inv                            | float64 |        0    |
| total_rec_prncp                            | float64 |        0    |
| total_rec_int                              | float64 |        0    |
| total_rec_late_fee                         | float64 |        0    |
| recoveries                                 | float64 |        0    |
| collection_recovery_fee                    | float64 |        0    |
| last_pymnt_d                               | str     |        0.11 |
| last_pymnt_amnt                            | float64 |        0    |
| next_pymnt_d                               | str     |       57.66 |
| last_credit_pull_d                         | str     |        0    |
| collections_12_mths_ex_med                 | int64   |        0.01 |
| mths_since_last_major_derog                | float64 |       74.31 |
| policy_code                                | int64   |        0    |
| application_type                           | str     |        0    |
| annual_inc_joint                           | float64 |       94.66 |
| dti_joint                                  | float64 |       94.66 |
| verification_status_joint                  | str     |       94.88 |
| acc_now_delinq                             | int64   |        0    |
| tot_coll_amt                               | int64   |        3.11 |
| tot_cur_bal                                | int64   |        3.11 |
| open_acc_6m                                | int64   |       38.31 |
| open_act_il                                | int64   |       38.31 |
| open_il_12m                                | int64   |       38.31 |
| open_il_24m                                | int64   |       38.31 |
| mths_since_rcnt_il                         | float64 |       40.25 |
| total_bal_il                               | int64   |       38.31 |
| il_util                                    | float64 |       47.28 |
| open_rv_12m                                | int64   |       38.31 |
| open_rv_24m                                | int64   |       38.31 |
| max_bal_bc                                 | int64   |       38.31 |
| all_util                                   | float64 |       38.32 |
| total_rev_hi_lim                           | int64   |        3.11 |
| inq_fi                                     | int64   |       38.31 |
| total_cu_tl                                | int64   |       38.31 |
| inq_last_12m                               | int64   |       38.31 |
| acc_open_past_24mths                       | int64   |        2.21 |
| avg_cur_bal                                | float64 |        3.11 |
| bc_open_to_buy                             | float64 |        3.31 |
| bc_util                                    | float64 |        3.36 |
| chargeoff_within_12_mths                   | int64   |        0.01 |
| delinq_amnt                                | int64   |        0    |
| mo_sin_old_il_acct                         | float64 |        6.15 |
| mo_sin_old_rev_tl_op                       | int64   |        3.11 |
| mo_sin_rcnt_rev_tl_op                      | int64   |        3.11 |
| mo_sin_rcnt_tl                             | int64   |        3.11 |
| mort_acc                                   | int64   |        2.21 |
| mths_since_recent_bc                       | float64 |        3.25 |
| mths_since_recent_bc_dlq                   | float64 |       77.01 |
| mths_since_recent_inq                      | float64 |       13.07 |
| mths_since_recent_revol_delinq             | float64 |       67.25 |
| num_accts_ever_120_pd                      | int64   |        3.11 |
| num_actv_bc_tl                             | int64   |        3.11 |
| num_actv_rev_tl                            | int64   |        3.11 |
| num_bc_sats                                | int64   |        2.59 |
| num_bc_tl                                  | int64   |        3.11 |
| num_il_tl                                  | int64   |        3.11 |
| num_op_rev_tl                              | int64   |        3.11 |
| num_rev_accts                              | int64   |        3.11 |
| num_rev_tl_bal_gt_0                        | int64   |        3.11 |
| num_sats                                   | int64   |        2.59 |
| num_tl_120dpd_2m                           | float64 |        6.8  |
| num_tl_30dpd                               | int64   |        3.11 |
| num_tl_90g_dpd_24m                         | int64   |        3.11 |
| num_tl_op_past_12m                         | int64   |        3.11 |
| pct_tl_nvr_dlq                             | float64 |        3.12 |
| percent_bc_gt_75                           | float64 |        3.33 |
| pub_rec_bankruptcies                       | int64   |        0.06 |
| tax_liens                                  | int64   |        0    |
| tot_hi_cred_lim                            | int64   |        3.11 |
| total_bal_ex_mort                          | int64   |        2.21 |
| total_bc_limit                             | int64   |        2.21 |
| total_il_high_credit_limit                 | int64   |        3.11 |
| revol_bal_joint                            | float64 |       95.22 |
| sec_app_earliest_cr_line                   | str     |       95.22 |
| sec_app_inq_last_6mths                     | float64 |       95.22 |
| sec_app_mort_acc                           | float64 |       95.22 |
| sec_app_open_acc                           | float64 |       95.22 |
| sec_app_revol_util                         | float64 |       95.3  |
| sec_app_open_act_il                        | float64 |       95.22 |
| sec_app_num_rev_accts                      | float64 |       95.22 |
| sec_app_chargeoff_within_12_mths           | float64 |       95.22 |
| sec_app_collections_12_mths_ex_med         | float64 |       95.22 |
| sec_app_mths_since_last_major_derog        | float64 |       98.41 |
| hardship_flag                              | str     |        0    |
| hardship_type                              | str     |       99.53 |
| hardship_reason                            | str     |       99.53 |
| hardship_status                            | str     |       99.53 |
| deferral_term                              | float64 |       99.53 |
| hardship_amount                            | float64 |       99.53 |
| hardship_start_date                        | str     |       99.53 |
| hardship_end_date                          | str     |       99.53 |
| payment_plan_start_date                    | str     |       99.53 |
| hardship_length                            | float64 |       99.53 |
| hardship_dpd                               | float64 |       99.53 |
| hardship_loan_status                       | str     |       99.53 |
| orig_projected_additional_accrued_interest | float64 |       99.63 |
| hardship_payoff_balance_amount             | float64 |       99.53 |
| hardship_last_payment_amount               | float64 |       99.53 |
| disbursement_method                        | str     |        0    |
| debt_settlement_flag                       | str     |        0    |
| debt_settlement_flag_date                  | str     |       98.54 |
| settlement_status                          | str     |       98.54 |
| settlement_date                            | str     |       98.54 |
| settlement_amount                          | float64 |       98.54 |
| settlement_percentage                      | float64 |       98.54 |
| settlement_term                            | float64 |       98.54 |

