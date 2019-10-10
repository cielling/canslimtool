from __future__ import print_function
import pandas as pd
from bs4 import BeautifulSoup as BSoup

from CanslimParams import CanslimParams

def areEqual(expect, val, eps = 0.01):
    try:
        diff = abs(float(val) / float(expect) - 1.0)
        assert diff < eps, "Values don't match, expected= {:.12f}, found= {:.12f}, diff= {:.12f}.\n".format(expect, val, diff)
        assert expect * val >= 0.0, "Values don't have the same sign: expected= {:f}, found= {:f}.\n".format(expect, val)
    except BaseException as be:
        print(be)

all10Ks = pd.read_csv("TestData\\nrp_all_10ks.csv", parse_dates=['date'], dtype={'cik':str, 'conm':str, 'type':str,'path':str})
all10Qs = pd.read_csv("TestData\\nrp_all_10qs.csv", parse_dates=['date'], dtype={'cik':str, 'conm':str, 'type':str,'path':str})

## Most recent filing in TestData: 2019 Q1
NvdaCanslimParams= CanslimParams("NRP", all10Qs, all10Ks)
## Load the data, and proceed if successful.
if NvdaCanslimParams.loadData("TestData"):
    ## Test all the EPS stuff
    ## Test the last four quarters to cover the case where the 10-K was filed instead of the 10-Q.
    print("Getting EPS for Q0:")
    expect = 2.26
    val = NvdaCanslimParams.getEpsQuarter(0)
    areEqual(expect, val)
    
    print("Getting EPS for Q-1:")
    expect = 8.77 - 1.71 - 2.46 - 1.49
    val = NvdaCanslimParams.getEpsQuarter(-1)
    areEqual(expect, val)
    
    print("Getting EPS for Q-2:")
    expect = 1.71
    val = NvdaCanslimParams.getEpsQuarter(-2)
    areEqual(expect, val)
    
    print("Getting EPS for Q-3:")
    expect = 0.0
    val = NvdaCanslimParams.getEpsQuarter(-3)
    areEqual(expect, val)
    
    ## Test the last two years of EPS
    print("Getting EPS for Y0:")
    expect = 8.77
    val = NvdaCanslimParams.getEpsAnnual(0)
    areEqual(expect, val)
    
    print("Getting EPS for Y-1:")
    expect = 5.06
    val = NvdaCanslimParams.getEpsAnnual(-1)
    areEqual(expect, val)
    
    print("Getting EPS growth for Q-3 to Q-4:")
    expect = 2.46 / 1.49 *100.0
    val = NvdaCanslimParams.getEpsGrowthQuarter(-3, -4)
    areEqual(expect, val)
    
    print("Getting EPS growth for Y0 to Y-1:")
    expect = 8.77/5.06*100.0
    val = NvdaCanslimParams.getEpsGrowthAnnual(0, -1)
    areEqual(expect, val)
    
    # print("Getting EPS growth rate for Q-3 to Q-4:")
    # expect = 
    # val = NvdaCanslimParams.getEpsGrowthRateQuarter(-4, -3)
    # areEqual(expect, val)
    
    # print("Getting EPS growth acceleration:")
    # expect = []
    # val = NvdaCanslimParams.getEpsGrowthAcceleration(4)
    # for i in range(0,3):
        # print(i)
        # areEqual(expect[i], val[i])
    
    # print("Getting stability of EPS:")
    # expect = 
    # val = NvdaCanslimParams.getStabilityOfEpsGrowth(4)
    # areEqual(expect, val)
    

    ## Test the Sales stuff
    print("Getting sales for Q-2:")
    expect = 122360. - 28565. - 39123. - 26088.
    val = NvdaCanslimParams.getSalesQuarter(-2)
    areEqual(expect, val)
    
    print("Getting sales for Y-1:")
    expect = 89208.0
    val = NvdaCanslimParams.getSalesAnnual(-1)
    areEqual(expect, val)
    
    print("Getting sales growth between Q0 and Q-2:")
    expect = 19106./(122360. - 28565. - 39123. - 26088.)*100.
    val = NvdaCanslimParams.getSalesGrowthQuarter(0, -2)
    areEqual(expect, val)
    
    # print("Getting sales growth rate between Q0 and Q-2:")
    # expect = 
    # val = NvdaCanslimParams.getSalesGrowthRateQuarter(-2, 0)
    # areEqual(expect, val)
    
    # print("Getting sales growth acceleration:")
    # expect = []
    # val = NvdaCanslimParams.getSalesGrowthAcceleration(4)
    # for i in range(0,3):
        # areEqual(expect[i], val[i])
    

    ## Test the ROE - delta net income/ delta stockholder's equity
    print("Getting current ROE:")
    expect = (19106. - 39123.) / (11614. - 30105.)
    val = NvdaCanslimParams.getRoeCurrent()
    areEqual(expect, val)
    

    ## Test the auxiliary functions
    
else:
    print("Unable to load data for NRP")
    NvdaCanslimParams.logErrors()

del NvdaCanslimParams