from __future__ import print_function
import pandas as pd
from bs4 import BeautifulSoup as BSoup
from sys import path as syspath
syspath.insert(0, "..")
from CanslimParams import CanslimParams
from myAssert import areEqual
from os import path as ospath


testDir = ospath.join("..", "TestData")
all10Ks = pd.read_csv(ospath.join(testDir, "nrp_all_10ks.csv"), parse_dates=['date'], dtype={'cik':str, 'conm':str, 'type':str,'path':str})
all10Qs = pd.read_csv(ospath.join(testDir, "nrp_all_10qs.csv"), parse_dates=['date'], dtype={'cik':str, 'conm':str, 'type':str,'path':str})

## Most recent filing in TestData: 2019 Q1
NRPCanslimParams= CanslimParams("NRP", all10Qs, all10Ks)
## Load the data, and proceed if successful.
if NRPCanslimParams.loadData(testDir):
    ## Test all the EPS stuff
    ## Test the last four quarters to cover the case where the 10-K was filed instead of the 10-Q.
    print("Getting EPS for Q0:")
    expect = 2.26
    val = NRPCanslimParams.getEpsQuarter(0)
    areEqual(expect, val)
    
    print("Getting EPS for Q-1:")
    expect = 8.77 - 1.71 - 2.46 - 1.49
    val = NRPCanslimParams.getEpsQuarter(-1)
    areEqual(expect, val)
    
    print("Getting EPS for Q-2:")
    expect = 1.71
    val = NRPCanslimParams.getEpsQuarter(-2)
    areEqual(expect, val)
    
    print("Getting EPS for Q-3:")
    expect = 0.0
    val = NRPCanslimParams.getEpsQuarter(-3)
    areEqual(expect, val)
    
    ## Test the last two years of EPS
    print("Getting EPS for Y0:")
    expect = 8.77
    val = NRPCanslimParams.getEpsAnnual(0)
    areEqual(expect, val)
    
    print("Getting EPS for Y-1:")
    expect = 5.06
    val = NRPCanslimParams.getEpsAnnual(-1)
    areEqual(expect, val)
    
    print("Getting EPS growth for Q-3 to Q-4:")
    expect = 2.46 / 1.49 *100.0
    val = NRPCanslimParams.getEpsGrowthQuarter(-3, -4)
    areEqual(expect, val)
    
    print("Getting EPS growth for Y0 to Y-1:")
    expect = 8.77/5.06*100.0
    val = NRPCanslimParams.getEpsGrowthAnnual(0, -1)
    areEqual(expect, val)
    
    # print("Getting EPS growth rate for Q-3 to Q-4:")
    # expect = 
    # val = NRPCanslimParams.getEpsGrowthRateQuarter(-4, -3)
    # areEqual(expect, val)
    
    # print("Getting EPS growth acceleration:")
    # expect = []
    # val = NRPCanslimParams.getEpsGrowthAcceleration(4)
    # for i in range(0,3):
        # print(i)
        # areEqual(expect[i], val[i])
    
    # print("Getting stability of EPS:")
    # expect = 
    # val = NRPCanslimParams.getStabilityOfEpsGrowth(4)
    # areEqual(expect, val)
    

    ## Test the Sales stuff
    print("Getting sales for Q-2:")
    expect = 122360. - 28565. - 39123. - 26088.
    val = NRPCanslimParams.getSalesQuarter(-2)
    areEqual(expect, val)
    
    print("Getting sales for Y-1:")
    expect = 89208.0
    val = NRPCanslimParams.getSalesAnnual(-1)
    areEqual(expect, val)
    
    print("Getting sales growth between Q0 and Q-2:")
    expect = 19106./(122360. - 28565. - 39123. - 26088.)*100.
    val = NRPCanslimParams.getSalesGrowthQuarter(0, -2)
    areEqual(expect, val)
    
    # print("Getting sales growth rate between Q0 and Q-2:")
    # expect = 
    # val = NRPCanslimParams.getSalesGrowthRateQuarter(-2, 0)
    # areEqual(expect, val)
    
    # print("Getting sales growth acceleration:")
    # expect = []
    # val = NRPCanslimParams.getSalesGrowthAcceleration(4)
    # for i in range(0,3):
        # areEqual(expect[i], val[i])
    

    ## Test the ROE - delta net income/ delta stockholder's equity
    print("Getting current ROE:")
    expect = (19106. - 39123.) / (11614. - 30105.)
    val = NRPCanslimParams.getRoeTTM()
    areEqual(expect, val)
    

    ## Test the auxiliary functions
    
else:
    print("Unable to load data for NRP")
    NRPCanslimParams.logErrors()

del NRPCanslimParams