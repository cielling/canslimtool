from __future__ import print_function
import pandas as pd
from bs4 import BeautifulSoup as BSoup

from CanslimParams import CanslimParams
from SecFiling10Q import SecFiling10Q

def areEqual(expect, val, eps = 0.01):
    try:
        diff = abs(float(val) / float(expect) - 1.0)
        assert diff < eps, "Values don't match, expected= {:.12f}, found= {:.12f}, diff= {:.12f}.\n".format(expect, val, diff)
        assert expect * val >= 0.0, "Values don't have the same sign: expected= {:f}, found= {:f}.\n".format(expect, val)
    except BaseException as be:
        print(be)


all10Ks = pd.read_csv("TestData\\aapl_all_10ks.csv", parse_dates=['date'], dtype={'cik':str, 'conm':str, 'type':str,'path':str})
all10Qs = pd.read_csv("TestData\\aapl_all_10qs.csv", parse_dates=['date'], dtype={'cik':str, 'conm':str, 'type':str,'path':str})

# test10Q = SecFiling10Q("AAPL")
# test10Q.load("TestData\\APPLE INC\\320193_APPLE INC_10-Q_2018-08-000000")
# print(test10Q.getEps())
# contextId = test10Q.getCurrentContextId()
# print("current context id: ", contextId)
# print("Sales= ", test10Q.getSales(contextId))

canslim= CanslimParams("AAPL", all10Qs, all10Ks)
## Load the data, and proceed if successful.
if canslim.loadData("TestData"):
    ## Test all the EPS stuff
    ## Test the last four quarters to cover the case where the 10-K was filed instead of the 10-Q.
    print("Getting EPS for Q0:")
    expect = 2.36
    val = canslim.getEpsQuarter(0)
    print(val)
    areEqual(expect, val)
    
    print("Getting EPS for Q-1:")
    expect = 2.75
    val = canslim.getEpsQuarter(-1)
    print(val)
    areEqual(expect, val)
    
    print("Getting EPS for Q-2:")
    expect = 3.92
    val = canslim.getEpsQuarter(-2)
    print(val)
    areEqual(expect, val)
    
    print("Getting EPS for Q-3:")
    expect = 2.18
    val = canslim.getEpsQuarter(-3)
    print(val)
    areEqual(expect, val)
    
    print("Getting EPS for Q-4:")
    expect = 1.68
    val = canslim.getEpsQuarter(-4)
    print(val)
    areEqual(expect, val)
    
    print("Getting EPS for Q-5:")
    expect = 2.11
    val = canslim.getEpsQuarter(-5)
    print(val)
    areEqual(expect, val)
    
    ## Test the last two years of EPS
    print("Getting EPS for Y0:")
    expect = 9.27
    val = canslim.getEpsAnnual(0)
    print(val)
    areEqual(expect, val)
    
    print("Getting EPS for Y-1:")
    expect = 8.35
    val = canslim.getEpsAnnual(-1)
    print(val)
    areEqual(expect, val)
    
    print("Getting EPS growth for Q-3 to Q-4:")
    expect = 2.18/1.68*100.0
    val = canslim.getEpsGrowthQuarter(-3, -4)
    print(val)
    areEqual(expect, val)
    
    print("Getting EPS growth for Y0 to Y-1:")
    expect = 9.27/8.35*100.0
    val = canslim.getEpsGrowthAnnual(0, -1)
    print(val)
    areEqual(expect, val)
    
    print("Getting EPS growth rate for Q-3 to Q-4:")
    expect = 0.00549450549451
    val = canslim.getEpsGrowthRateQuarter(-4, -3)
    print(val)
    areEqual(expect, val)
    
    print("Getting EPS growth acceleration:")
    expect = [ -6.43038280e-05, -1.82472527e-02, 2.17550000e+00]
    val = canslim.getEpsGrowthAcceleration(4)
    print(val)
    for i in range(0,3):
        print(i)
        areEqual(expect[i], val[i])
    
    print("Getting stability of EPS:")
    expect = 0.0737224063131
    val = canslim.getStabilityOfEpsGrowth(4)
    print(val)
    areEqual(expect, val)
    

    ## Test the Sales stuff
    print("Getting sales for Q-2:")
    expect = 88293000000.0
    val = canslim.getSalesQuarter(-2)
    print(val)
    areEqual(expect, val)
    
    print("Getting sales for Y-1:")
    expect = 215639000000.
    val = canslim.getSalesAnnual(-1)
    print(val)
    areEqual(expect, val)
    
    print("Getting sales growth between Q0 and Q-2:")
    expect = 53265.0/(88293.)*100.
    val = canslim.getSalesGrowthQuarter(0, -2)
    print(val)
    areEqual(expect, val)
    
    print("Getting sales growth rate between Q0 and Q-2:")
    expect = -192461538.462
    val = canslim.getSalesGrowthRateQuarter(-2, 0)
    print(val)
    areEqual(expect, val)
    
    print("Getting sales growth acceleration:")
    expect = [ -1.241003e+06, -3.74546703e+08, 4.91573000e+10]
    val = canslim.getSalesGrowthAcceleration(4)
    print(val)
    for i in range(0,3):
        areEqual(expect[i], val[i])
    

    # Test the ROE
    print("Getting current ROE:")
    expect = 11519.0/114949.0
    val = canslim.getRoeCurrent()
    print(val)
    areEqual(expect, val)
    

    ## Test the auxiliary functions
    
else:
    print("Unable to load data for NVDA")

del canslim