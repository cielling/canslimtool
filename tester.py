from __future__ import print_function
import pandas as pd
from bs4 import BeautifulSoup as BSoup

from CanslimParams import CanslimParams

all10Ks = pd.read_csv("TestData\\nvda_all_10ks.csv", parse_dates=['date'], dtype={'cik':str, 'conm':str, 'type':str,'path':str})
all10Qs = pd.read_csv("TestData\\nvda_all_10qs.csv", parse_dates=['date'], dtype={'cik':str, 'conm':str, 'type':str,'path':str})

NvdaCanslimParams= CanslimParams("NVDA", all10Qs, all10Ks)
## Load the data, and proceed if successful.
if NvdaCanslimParams.loadData():
    ## Test all the EPS stuff
    ## Test the last four quarters to cover the case where the 10-K was filed instead of the 10-Q.
    print("Getting EPS for Q0:")
    print(NvdaCanslimParams.getEpsQuarter(0))
    print("Getting EPS for Q-1:")
    print(NvdaCanslimParams.getEpsQuarter(-1))
    print("Getting EPS for Q-2:")
    print(NvdaCanslimParams.getEpsQuarter(-2))
    print("Getting EPS for Q-3:")
    print(NvdaCanslimParams.getEpsQuarter(-3))
    ## Test the last two years of EPS
    print("Getting EPS for Y0:")
    print(NvdaCanslimParams.getEpsAnnual(0))
    print("Getting EPS for Y-1:")
    print(NvdaCanslimParams.getEpsAnnual(-1))
    print("Getting EPS growth for Q-3 to Q-4:")
    print(NvdaCanslimParams.getEpsGrowthQuarter(-3, -4))
    print("Getting EPS for Y0 to Y-1:")
    print(NvdaCanslimParams.getEpsGrowthAnnual(0, -1))
    print("Getting stability of EPS:")
    print(NvdaCanslimParams.getStabilityOfEpsGrowth(4))
    print("Getting EPS growth acceleration:")
    print(NvdaCanslimParams.getEpsGrowthAcceleration(4))

    ## Test the Sales stuff
    print("Getting sales for Q-2:")
    print(NvdaCanslimParams.getSalesQuarter(-2))
    print("Getting EPS for Y-1:")
    print(NvdaCanslimParams.getSalesAnnual(-1))
    print("Getting sales growth between Q0 and Q-2:")
    print(NvdaCanslimParams.getSalesGrowth(0, -2))
    print("Getting sales growth acceleration:")
    print(NvdaCanslimParams.getSalesGrowthAcceleration(4))

    ## Test the ROE
    print("Getting current ROE:")
    print(NvdaCanslimParams.getRoeCurrent())

    ## Test the auxiliary functions

del NvdaCanslimParams