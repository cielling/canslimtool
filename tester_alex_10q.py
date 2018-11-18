from __future__ import print_function
import pandas as pd
from bs4 import BeautifulSoup as BSoup

from SecFiling10Q import SecFiling10Q

def areEqual(expect, val, eps = 0.01):
    try:
        diff = abs(float(val) / float(expect) - 1.0)
        assert diff < eps, "Values don't match, expected= {:.12f}, found= {:.12f}, diff= {:.12f}.\n".format(expect, val, diff)
        assert expect * val >= 0.0, "Values don't have the same sign: expected= {:f}, found= {:f}.\n".format(expect, val)
    except BaseException as be:
        print(be)

ticker = "ALEX"

all10Qs = pd.read_csv("TestData\\"+ticker.lower()+"_all_10qs.csv", \
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