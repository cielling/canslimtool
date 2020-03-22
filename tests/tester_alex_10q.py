from __future__ import print_function
import pandas as pd
from bs4 import BeautifulSoup as BSoup
from sys import path as syspath
syspath.insert(0, "..")
from CanslimParams import CanslimParams
from myAssert import areEqual
from os import path as ospath


testDir = ospath.join("..", "TestData")
ticker = "ALEX"

all10Qs = pd.read_csv(ospath.join(testDir, "{:s}_all_10ks.csv".format(ticker.lower())), \
        dtype={'cik':str, 'conm':str, 'type':str, 'path':str, 'date':str})


testfile = all10Qs[all10Qs.date == "2018-05-10"]
filing = SecFiling10Q(ticker)
filename = filing.download(testfile.cik.iloc[0], testfile.conm.iloc[0], testfile.type.iloc[0], \
        testfile.date.iloc[0], testfile.path.iloc[0], downloadPath = "TestData\\")
## Load the data, and proceed if successful.
if filing.load(filename):
    print("Verifying EPS")
    areEqual(0.71, filing.getEps())
    
    print("Verifying Sales")
    areEqual(113.3*1e6, filing.getSales())
    
    print("Verifying ROE")
    areEqual(47.3/1320.6, filing.getRoe())
    
    print("Verifying Net Income")
    areEqual(47.3*1e6, filing.getNetIncome())
    
    print("Verifying Stockholders' Equity")
    areEqual(1320.6*1e6, filing.getStockholdersEquity())