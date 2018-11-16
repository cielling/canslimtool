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

all10Ks = pd.read_csv("TestData\\acls_all_10ks.csv", parse_dates=['date'], dtype={'cik':str, 'conm':str, 'type':str,'path':str})
all10Qs = pd.read_csv("TestData\\acls_all_10qs.csv", parse_dates=['date'], dtype={'cik':str, 'conm':str, 'type':str,'path':str})

ticker = "ACLS"

canslim= CanslimParams(ticker, all10Qs, all10Ks)
## Load the data, and proceed if successful.
if canslim.loadData("TestData"):
    ## Test all the EPS stuff
    ## Test the last four quarters to cover the case where the 10-K was filed instead of the 10-Q.
    print("Getting EPS for Q0:")
    expect = 0.46
    val = canslim.getEpsQuarter(0)
    areEqual(expect, val)
    
    print("Getting EPS for Q-1:")
    expect = 0.43
    val = canslim.getEpsQuarter(-1)
    areEqual(expect, val)
    
    print("Getting EPS for Q-2:")
    expect = 2.95
    val = canslim.getEpsQuarter(-2)
    areEqual(expect, val)
    
    ## Test the last two years of EPS
    print("Getting EPS for Y0:")
    expect = 4.11
    val = canslim.getEpsAnnual(0)
    areEqual(expect, val)
    
    print("Getting EPS for Y-1:")
    expect = 0.38
    val = canslim.getEpsAnnual(-1)
    areEqual(expect, val)
    
    print("Getting EPS growth for Q-1 to Q-2:")
    expect = 0.43/2.95*100.0
    val = canslim.getEpsGrowthQuarter(-1, -2)
    areEqual(expect, val)
    
    print("Getting EPS growth for Y0 to Y-1:")
    expect = 4.11/0.38 * 100.0
    val = canslim.getEpsGrowthAnnual(0, -1)
    areEqual(expect, val)
    
    print("Getting EPS growth rate for Q-2 to Q-1:")
    expect = -0.02800
    val = canslim.getEpsGrowthRateQuarter(-2, -1)
    areEqual(expect, val)
    

    ## Test the Sales stuff
    print("Getting sales for Q-2:")
    expect = 116396000.0
    val = canslim.getSalesQuarter(-2)
    areEqual(expect, val)
    
    print("Getting sales for Y-1:")
    expect = 266980000.0
    val = canslim.getSalesAnnual(-1)
    areEqual(expect, val)
    
    print("Getting sales growth between Q0 and Q-2:")
    expect = 102.5232825
    val = canslim.getSalesGrowthQuarter(0, -2)
    areEqual(expect, val)
    
    print("Getting sales growth rate between Q0 and Q-2:")
    expect = 16226.519337
    val = canslim.getSalesGrowthRateQuarter(-2, 0)
    areEqual(expect, val)
    

    ## Test the ROE
    print("Getting current ROE:")
    expect = 14669.0/385614.0
    val = canslim.getRoeCurrent()
    areEqual(expect, val)
    

    ## Test the auxiliary functions
    
else:
    print("Unable to load data for {:s}".format(ticker))

del canslim