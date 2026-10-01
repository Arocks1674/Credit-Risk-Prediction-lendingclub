# Model comparison (out-of-time test set)

Train: 574,179 loans issued before Sep 2015. Test: 155,296 loans issued Sep 2015 to Feb 2016. Test default rate 15.0%.

|                                  |   roc_auc |   train_roc_auc |   gini |     ks |   pr_auc |   brier |   log_loss |   mean_pd |   default_rate |
|:---------------------------------|----------:|----------------:|-------:|-------:|---------:|--------:|-----------:|----------:|---------------:|
| LendingClub sub-grade only       |    0.6853 |          0.6671 | 0.3707 | 0.2711 |   0.2618 |  0.1209 |     0.3961 |    0.1329 |         0.1500 |
| Logistic regression              |    0.6992 |          0.6888 | 0.3984 | 0.2935 |   0.2775 |  0.1197 |     0.3917 |    0.1340 |         0.1500 |
| Logistic + class weights         |    0.6991 |          0.6888 | 0.3982 | 0.2933 |   0.2766 |  0.2054 |     0.5959 |    0.4340 |         0.1500 |
| Logistic, SMOTE subset, no SMOTE |    0.6981 |          0.6881 | 0.3963 | 0.2919 |   0.2767 |  0.1198 |     0.3921 |    0.1333 |         0.1500 |
| Logistic + SMOTE                 |    0.6932 |          0.6841 | 0.3864 | 0.2809 |   0.2716 |  0.1988 |     0.5795 |    0.4171 |         0.1500 |
| XGBoost                          |    0.7060 |          0.7167 | 0.4119 | 0.3012 |   0.2903 |  0.1188 |     0.3889 |    0.1336 |         0.1500 |
| XGBoost without LC grade/rate    |    0.6920 |          0.7079 | 0.3841 | 0.2781 |   0.2793 |  0.1202 |     0.3942 |    0.1306 |         0.1500 |
| MLP (ANN)                        |    0.7056 |          0.7001 | 0.4111 | 0.2994 |   0.2885 |  0.1186 |     0.3880 |    0.1426 |         0.1500 |


XGBoost chosen on validation: {"max_depth": 5, "min_child_weight": 50, "val_auc": 0.698294252826779, "trees": 403, "trees_refit": 443}

MLP epochs chosen on validation: 9

SMOTE was run on a 150,000-loan random subset of training data (memory).

## XGBoost validation grid

|   max_depth |   min_child_weight |   val_auc |    trees |
|------------:|-------------------:|----------:|---------:|
|      3.0000 |             1.0000 |    0.6970 | 761.0000 |
|      3.0000 |            50.0000 |    0.6977 | 797.0000 |
|      5.0000 |             1.0000 |    0.6973 | 330.0000 |
|      5.0000 |            50.0000 |    0.6983 | 403.0000 |
|      7.0000 |             1.0000 |    0.6969 | 164.0000 |
|      7.0000 |            50.0000 |    0.6977 | 202.0000 |

