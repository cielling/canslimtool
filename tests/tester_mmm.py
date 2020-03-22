from __future__ import print_function
import pandas as pd
from bs4 import BeautifulSoup as BSoup
from CanslimParams import CanslimParams
import numpy as np
from datetime import date, timedelta, datetime
#from datetime import datetime.now as now
from myAssert import areEqual
from os import path as ospath
from sys import path as syspath
syspath.insert(0, "..")

## "current date" = 2019 Q1
currentDate = date(2019,2,1)

ticker = "MMM"

## Data from SEC-filings
## 10-Q's
epsQ = np.array([1.54, 2.3, 2.64, 3.14, 1.01, 0.88, 2.39, 2.65, 2.21, 1.92, 2.2, 2.13, 2.1, 1.69, 2.09, 2.06, 1.88])
datesQ = np.array([date(2019, 3, 31), date(2018, 12, 31), date(2018, 9, 30), date(2018, 6, 30), date(2018, 3, 31), date(2017, 12, 31), date(2017, 9, 30), date(2017, 6, 30), date(2017, 3, 31), date(2016, 12, 31), date(2016, 9, 30), date(2016, 6, 30), date(2016, 3, 31), date(2015, 12, 31), date(2015, 9, 30), date(2015, 6, 30), date(2015, 3, 31)])
salesQ = np.array([7863000000, 7945000000, 8152000000, 8390000000, 8278000000, 8008000000, 8172000000, 7810000000, 7685000000, 7329000000, 7709000000, 7662000000, 7409000000, 7298000000, 7712000000, 7686000000, 7578000000])
seQ = np.array([9703000000, 10407000000, 10248000000, 10365000000, 10977000000, 11672000000, 12146000000, 11591000000, 10989000000, 11316000000, 12002000000, 11894000000, 11733000000, 12484000000, 12186000000, 13093000000, 13917000000])
niQ = np.array([891000000, 1361000000, 1543000000, 1857000000, 602000000, 534000000, 1429000000, 1583000000, 1323000000, 1163000000, 1329000000, 1291000000, 1275000000, 1041000000, 1296000000, 1303000000, 1201000000])
delta = datesQ - datesQ[0]
l = []
for d in delta:
    l.append(d.days)
daysQ = np.array(l)

## 10-K's
epsY = np.array([9.09, 8.13, 8.35, 7.72])
datesY = np.array([date(2018, 12, 31), date(2017, 12, 31), date(2016, 12, 31), date(2015, 12, 31)])
salesY = np.array([32765000000, 31675000000, 30109000000, 30274000000])
seY = np.array([10407000000, 11672000000, 11316000000, 12484000000])
niY = np.array([5363000000, 4869000000, 5058000000, 4841000000])
delta = datesY - datesY[0]
l = []
for d in delta:
    l.append(d.days)
daysY = np.array(l)


print("Testing ticker {:s}".format(ticker))

testDir = ospath.join("..", "TestData")
all10Ks = pd.read_csv(ospath.join(testDir, "{:s}_all_10ks.csv".format(ticker.lower())), parse_dates=['date'], dtype={'cik':str, 'conm':str, 'type':str,'path':str})
all10Qs = pd.read_csv(ospath.join(testDir, "{:s}_all_10qs.csv".format(ticker.lower())), parse_dates=['date'], dtype={'cik':str, 'conm':str, 'type':str,'path':str})

canslim= CanslimParams(ticker, all10Qs, all10Ks)
## Load the data, and proceed if successful.
oldestDate = datetime(2014, 1, 1)
if canslim.loadData(testDir, oldestDate):
    ## Test all the EPS stuff
    for q in range(0, len(epsQ)):
        print("Getting EPS for quarter {:d}".format(q))
        value = canslim.getEpsQuarter(-q)
        areEqual(epsQ[q], value)
    
    for y in range(0, len(epsY)):
        print("Getting EPS for year {:d}".format(y))
        value = canslim.getEpsAnnual(-y)
        areEqual(epsY[y], value)
            
    print("Getting EPS growth for Q-1 to Q-2:")
    expect = epsQ[1] / epsQ[2] * 100.0
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
    for q in range(0, len(salesQ)):
        print("Getting SALES for quarter {:d}".format(q))
        value = canslim.getSalesQuarter(-q)
        areEqual(salesQ[q], value)
    
    for y in range(0, len(salesY)):
        print("Getting SALES for year {:d}".format(y))
        value = canslim.getSalesAnnual(-y)
        areEqual(salesY[y], value)
    
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
    expect = np.sum(niQ[0:4]) / np.average(seQ[0:4]) * 100.0
    val = canslim.getRoeTTM()
    areEqual(expect, val)
    
    print("Getting stability of EPS - last 12 Q:")
    expect = 3.2385
    val = canslim.getStabilityOfEpsGrowth(12)
    areEqual(expect, val)
    

    ## Test the auxiliary functions
    
    ## Print all errors that were logged.
    canslim.logErrors()
    print("Errors written to Logs/{:s}_log.txt".format(ticker))
    
else:
    print("Unable to load data for {:s}".format(ticker))

del canslim