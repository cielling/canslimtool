from __future__ import print_function
import pandas as pd
from bs4 import BeautifulSoup as BSoup

## "current date" = 2019 Q1

from CanslimParams import CanslimParams

def areEqual(expect, val, eps = 0.01):
    print("Expected: ", expect, " actual: ", val)
    try:
        diff = abs(float(val) / float(expect) - 1.0)
        assert diff < eps, "Values don't match, expected= {:.12f}, found= {:.12f}, diff= {:.12f}.\n".format(expect, val, diff)
        assert expect * val >= 0.0, "Values don't have the same sign: expected= {:f}, found= {:f}.\n".format(expect, val)
    except BaseException as be:
        print(be)

ticker = "MMM"

print("Testing ticker {:s}".format(ticker))

all10Ks = pd.read_csv("TestData\\" + ticker.lower() + "_all_10ks.csv", parse_dates=['date'], dtype={'cik':str, 'conm':str, 'type':str,'path':str})
all10Qs = pd.read_csv("TestData\\" + ticker.lower() + "_all_10qs.csv", parse_dates=['date'], dtype={'cik':str, 'conm':str, 'type':str,'path':str})

canslim= CanslimParams(ticker, all10Qs, all10Ks)
## Load the data, and proceed if successful.
if canslim.loadData("TestData"):
    ## Test all the EPS stuff
    ## Test the last four quarters to cover the case where the 10-K was filed instead of the 10-Q.
    print("Getting EPS for Q0:")
    expect = 1.54
    val = canslim.getEpsQuarter(0)
    areEqual(expect, val)
    
    print("Getting EPS for Q-1:")
    expect = 9.09 - 2.64 - 3.14 - 1.01
    val = canslim.getEpsQuarter(-1)
    areEqual(expect, val)
    
    print("Getting EPS for Q-2:")
    expect = 2.64
    val = canslim.getEpsQuarter(-2)
    areEqual(expect, val)
    
    ## Test the last two years of EPS
    print("Getting EPS for Y0:")
    expect = 9.09
    val = canslim.getEpsAnnual(0)
    areEqual(expect, val)
    
    print("Getting EPS for Y-1:")
    expect = 8.13
    val = canslim.getEpsAnnual(-1)
    areEqual(expect, val)
    
    print("Getting EPS growth for Q-1 to Q-2:")
    expect = (9.09 - 2.64 - 3.14 - 1.01) / 2.64 * 100.0
    val = canslim.getEpsGrowthQuarter(-1, -2)
    areEqual(expect, val)
    
    # print("Getting EPS growth for Y0 to Y-1:")
    # expect = -0.37/-2.58
    # val = canslim.getEpsGrowthAnnual(0, -1)
    # areEqual(expect, val)
    
    # print("Getting EPS growth rate for Q-2 to Q-1:")
    # expect = 0.
    # val = canslim.getEpsGrowthRateQuarter(-2, -1)
    # areEqual(expect, val)
    

    ## Test the Sales stuff
    print("Getting sales for Q-2:")
    expect = 8152000000.0
    val = canslim.getSalesQuarter(-2)
    areEqual(expect, val)
    
    print("Getting sales for Y-1:")
    expect = 31675000000.0
    val = canslim.getSalesAnnual(-1)
    areEqual(expect, val)
    
    # print("Getting sales growth between Q0 and Q-2:")
    # expect = 0.
    # val = canslim.getSalesGrowthQuarter(0, -2)
    # areEqual(expect, val)
    
    # print("Getting sales growth rate between Q0 and Q-2:")
    # expect = 0.
    # val = canslim.getSalesGrowthRateQuarter(-2, 0)
    # areEqual(expect, val)
    

    ## Test the ROE
    print("Getting current ROE (TTM):")
    expect = (891000000 + 5363000000 - 602000000) / (9703000000 + 10407000000 + 10248000000 + 10365000000) * 4 * 100.0
    val = canslim.getRoeTTM()
    areEqual(expect, val)
    

    ## Test the auxiliary functions
    
    ## Print all errors that were logged.
    canslim.logErrors()
    print("Errors written to Logs/{:s}_log.txt".format(ticker))
    
else:
    print("Unable to load data for {:s}".format(ticker))

del canslim