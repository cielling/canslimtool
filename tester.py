from __future__ import print_function
import pandas as pd
from bs4 import BeautifulSoup as BSoup

from CanslimParams import CanslimParams

all10Ks = pd.read_csv("TestData\\nvda_all_10ks.csv", parse_dates=['date'], dtype={'cik':str, 'conm':str, 'type':str,'path':str})
all10Qs = pd.read_csv("TestData\\nvda_all_10qs.csv", parse_dates=['date'], dtype={'cik':str, 'conm':str, 'type':str,'path':str})

NvdaCanslimParams= CanslimParams("NVDA", all10Qs, all10Ks)
NvdaCanslimParams.loadData()
NvdaCanslimParams.getEpsQuarter(0)
NvdaCanslimParams.getEpsAnnual(-1)
NvdaCanslimParams.getSalesQuarter(-2)
NvdaCanslimParams.getSalesAnnual(-2)
NvdaCanslimParams.getRoeCurrent()
NvdaCanslimParams.getEpsGrowthQuarter(-3, -4)
NvdaCanslimParams.getEpsGrowthAnnual(0, -1)
NvdaCanslimParams.getStabilityOfEpsGrowth(4)
NvdaCanslimParams.getEpsGrowthAcceleration(4)

Canslim = {}
Canslim['Eps_current_Q_per_same_Q_prior_year'] = -99
Canslim['Sales_current_Q_per_prior_Q'] = -99
Canslim['Sales_growth_accel_last_3_Q'] = -99
Canslim['Eps_growth_accel_last_3_Q'] = -99
Canslim['Stability_of_Q_eps_growth_last_3_years'] = -99
Canslim['Excellency_of_eps_increase'] = -99
Canslim['Num_Q_with_eps_growth_deceleration'] = -99
Canslim['Num_years_annual_eps_increasing_last_3_years'] = -99