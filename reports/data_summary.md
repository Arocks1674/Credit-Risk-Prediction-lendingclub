# Modelling data

Source: `loan.csv`  |  data snapshot: Feb 2019

## From raw rows to the modelling table

|                               |     loans |   default_rate_% |
|:------------------------------|----------:|-----------------:|
| all rows                      | 2260668.0 |            nan   |
| finished (paid / charged off) | 1303638.0 |             20.1 |
| matured by Feb 2019           |  729475.0 |             15.0 |


## Matured loans by issue year

|   issue_date |    loans |   default_rate_pct |
|-------------:|---------:|-------------------:|
|         2007 |    251.0 |               17.9 |
|         2008 |   1562.0 |               15.8 |
|         2009 |   4716.0 |               12.6 |
|         2010 |  11536.0 |               12.9 |
|         2011 |  21721.0 |               15.2 |
|         2012 |  53367.0 |               16.2 |
|         2013 | 134793.0 |               15.6 |
|         2014 | 170643.0 |               14.3 |
|         2015 | 282853.0 |               14.9 |
|         2016 |  48033.0 |               15.5 |


## By term

|   term_months |      loans |   default_rate |
|--------------:|-----------:|---------------:|
|        36.000 | 666444.000 |          0.140 |
|        60.000 |  63031.000 |          0.254 |


## Out-of-time split

|                    |   loans | issued               |   default_rate_% |
|:-------------------|--------:|:---------------------|-----------------:|
| train              |  574179 | Jun 2007 to Aug 2015 |             15.0 |
| test (out-of-time) |  155296 | Sep 2015 to Feb 2016 |             15.0 |

