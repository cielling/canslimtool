from numpy import polyfit, polyval
import requests
from bs4 import BeautifulSoup as BSoup
import pandas as pd
import csv
import requests
import os
from datetime import datetime, timedelta
from SecFiling10Q import SecFiling10Q
from SecFiling10K import SecFiling10K

class CanslimParams():
    def __init__(self, ticker, all10QsDf, all10KsDf):
        self.ticker = ticker
        ## Format the 'date' column into datetime format
        self.all10QsDf = all10QsDf
        self.all10KsDf = all10KsDf
        self.today = datetime.now()
        self.fiveYearsAgo = self.today - timedelta(days=5*365.25)
        self.currentQ = ""
        self.currentY = ""
        self.quartersList = []
        self.yearsList = []
        self.all10QFilings = {}
        self.all10KFilings = {}
        self.savedContextIds = {}

        
    def loadData(self):
        """Loads the relevant SEC filings for analysis.
        
        Loads the last 4 10-K filings and the last 16(?) 10-Q filings. If necessary, 
        retrieves them from EDGAR and saves the raw files.
        """
        ## TODO: Look through the idx database and find all filings available for 'ticker'. -> in main()
        self.all10QFilings = {}
        self.all10KFilings = {}
        n10Qs = len(self.all10QsDf)
        n10Ks = len(self.all10KsDf)
        ## The following loops lend themselves to parallelizing, if that's possible
        ## Create a dict of all the 10Q-filings objects
        mostRecentDate = self.fiveYearsAgo
        for i in range(0, n10Qs):
            if (self.all10QsDf.iloc[i].date > self.fiveYearsAgo):
                filing = SecFiling10Q(self.ticker)
                ## Download file if necessary, and generate the file name
                fname = filing.download(self.all10QsDf.iloc[i].cik, \
                                        self.all10QsDf.iloc[i].conm, \
                                        self.all10QsDf.iloc[i].type, \
                                        self.all10QsDf.iloc[i].date.strftime("%Y-%m-%f"), \
                                        self.all10QsDf.iloc[i].path)
                ## Load the file into the object instance
                filing.load(fname)
                ## Use the year+quarter (for filing date) information to create a key into the dict
                quarterKey = "{:d}-Q{:d}".format(self.all10QsDf.iloc[i].date.year, int(self.all10QsDf.iloc[i].date.month / 3 + 1))
                ## TODO: verify that each filing was successfully loaded
                self.all10QFilings[quarterKey] = filing
                ## find the date of the most recent filing, to determine the "current quarter"
                if self.all10QsDf.iloc[i].date > mostRecentDate:
                    mostRecentDate = self.all10QsDf.iloc[i].date
                    self.currentQ = quarterKey
                    
        # Create a dict of all the 10K-filing objects:
        mostRecentDate = self.fiveYearsAgo
        for i in range(0, n10Ks):
            if (self.all10KsDf.iloc[i].date > self.fiveYearsAgo):
                filing = SecFiling10K(self.ticker)
                ## Download file if necessary, and generate the file name
                fname = filing.download(self.all10KsDf.iloc[i].cik, \
                                        self.all10KsDf.iloc[i].conm, \
                                        self.all10KsDf.iloc[i].type, \
                                        self.all10KsDf.iloc[i].date.strftime("%Y-%m-%f"), \
                                        self.all10KsDf.iloc[i].path)
                ## Load the file into the object instance
                filing.load(fname)
                ## Use the year+quarter (for filing date) information to create a key into the dict
                yearKey = "Y{:d}".format(self.all10KsDf.iloc[i].date.year)
                ## TODO: verify that each filing was successfully loaded
                self.all10KFilings[yearKey] = filing
                ## find the date of the most recent filing, to determine the "current year"
                if self.all10KsDf.iloc[i].date > mostRecentDate:
                    mostRecentDate = self.all10KsDf.iloc[i].date
                    self.currentY = yearKey
        return True
    
                
    def _getQuarter(self, q):
        """Returns the quarter-key for the requested quarter in the past.
        
        The format of the quarter-key is 'Ynnnn-Qm' and is intended to be used to index into the all10QFilings-dict of 
        SecFiling10Q instances.
        """
        if abs(q) > 20:
            return None
        if not self.quartersList:
            currentYear = int(self.currentQ.split("-Q")[0])
            currentQuarter = int(self.currentQ.split("-Q")[1])
            self.quartersList.append(self.currentQ)
            quarter = currentQuarter
            year = currentYear
            for i in range(0,20):
                quarter = quarter - 1
                if quarter < 1:
                    quarter = quarter + 4
                    year = year - 1
                self.quartersList.append("{:d}-Q{:d}".format(year, quarter))
        return self.quartersList[abs(q)]
    
    
    def _getYear(self, y):
        """Returns the year-key for the requested year in the past.
        
        The format of the year-key is 'Ynnnn' and is intended to be used to index into the all10KFilings-dict of 
        SecFiling10K instances.
        """
        if abs(y) > 5:
            return None
        if not self.yearsList:
            currentYear = int(self.currentY[1:])
            for i in range(0,5):
                year = currentYear - i
                self.yearsList.append("Y{:d}".format(year))
        return self.yearsList[abs(y)]
    
    
    def getEpsQuarter(self, quarter):
        """Returns the EPS for the specified quarter.
        
        The quarter is specified as an integer counting backwards, e.g. 0 (zero) is the current quarter,
        -1 (minus one) is the previous quarter, etc. For readability, the minus sign is required. Only 
        integers between -15 and 0 are allowed.
        """
        if quarter > -20:
            qKey = self._getQuarter(quarter)
            try:
                eps = (self.all10QFilings)[qKey].getEps()
                ## This is annoying, but save the current contextId for use in getSales later
                self.savedContextIds[qKey] = self.all10QFilings[qKey].getCurrentContextId()
            except KeyError:
                ## Some/most/all? companies submit the 10-K *instead* of the 10-Q for that quarter.
                ## So I have to calculate the values for that quarter from the 10-K and preceding 3 10-Q's.
                ## If the missing Q is Q1, then the preceding 3 10's are from the prior year.
                ## Make sure we have all the historical data we need:
                if (quarter - 3) < -20:
                    return None
                year10KKey = "Y" + qKey[:4]
                yearEps = self.all10KFilings[year10KKey].getEps()
                self.savedContextIds[qKey] = self.all10KFilings[year10KKey].getCurrentContextId()
                
                last1QKey = self._getQuarter(quarter - 1)
                last1Eps = self.all10QFilings[last1QKey].getEps()
                self.savedContextIds[last1QKey] = self.all10QFilings[last1QKey].getCurrentContextId()
                
                last2QKey = self._getQuarter(quarter - 2)
                last2Eps = self.all10QFilings[last2QKey].getEps()
                self.savedContextIds[last2QKey] = self.all10QFilings[last2QKey].getCurrentContextId()
                
                last3QKey = self._getQuarter(quarter - 3)
                last3Eps = self.all10QFilings[last3QKey].getEps()
                self.savedContextIds[last3QKey] = self.all10QFilings[last3QKey].getCurrentContextId()
                
                eps = yearEps - last1Eps - last2Eps - last3Eps
            return eps
        return None
    
    
    def getEpsAnnual(self, year):
        """Returns the EPS for the specified year.
        
        The year is specified as an integer counting backwards, e.g. 0 (zero) is the most recent reported year,
        -1 (minus one) is the previous year, etc. For readability, the minus sign is required. Only 
        integers between -3 and 0 are allowed.
        """
        if year > -5:
            yKey = self._getYear(year)
            eps = self.all10KFilings[yKey].getEps()
            self.savedContextIds[yKey] = self.all10KFilings[yKey].getCurrentContextId()
            return eps
        return None
    
    
    def getRoeCurrent(self):
        """Returns the most recent Return on Equity."""
        return self.all10QFilings[self.currentQ].getRoe()
    
    
    def getSalesQuarter(self, quarter):
        """Returns the Sales for the specified quarter.
        
        The quarter is specified as an integer counting backwards, e.g. 0 (zero) is the current quarter,
        -1 (minus one) is the previous quarter, etc. For readability, the minus sign is required. Only 
        integers between -15 and 0 are allowed.
        """
        if quarter > -20:
            qKey = self._getQuarter(quarter)
            try:
                sales = self.all10QFilings[qKey].getSales(self.savedContextIds[qKey])            
            except KeyError:
                ## Some/most/all? companies submit the 10-K *instead* of the 10-Q for that quarter.
                ## So I have to calculate the values for that quarter from the 10-K and preceding 3 10-Q's.
                ## If the missing Q is Q1, then the preceding 3 10's are from the prior year.
                ## Make sure we have all the historical data we need:
                if (quarter - 3) < -20:
                    return None
                year10KKey = "Y" + qKey[:4]
                last1QKey = self._getQuarter(quarter - 1)
                last2QKey = self._getQuarter(quarter - 2)
                last3QKey = self._getQuarter(quarter - 3)
                sales = self.all10KFilings[year10KKey].getSales(self.savedContextIds[year10KKey]) \
                        - self.all10QFilings[last1QKey].getSales(self.savedContextIds[last1QKey]) \
                        - self.all10QFilings[last2QKey].getSales(self.savedContextIds[last2QKey]) \
                        - self.all10QFilings[last3QKey].getSales(self.savedContextIds[last3QKey])
            return sales
        return None
    
    
    def getSalesAnnual(self, year):
        """Returns the Sales for the specified year.
        
        The year is specified as an integer counting backwards, e.g. 0 (zero) is the most recent reported year,
        -1 (minus one) is the previous year, etc. For readability, the minus sign is required. Only 
        integers between -3 and 0 are allowed.
        """
        if year > -5:
            yKey = self._getYear(year)
            return self.all10KFilings[yKey].getSales()
        return None
    
        
    def getEpsGrowthQuarter(self, q1, q2):
        """Calculates the EPS growth (%) for quarter q1 compared to q2.
        
        The EPS growth is calculated as the ratio EPS(q1)/EPS(q2) * 100%.
        """
        epsQ1 = self.getEpsQuarter(q1)
        epsQ2 = self.getEpsQuarter(q2)
        try:
            growth = (epsQ1 / epsQ2) * 100.
        except:
            print("Unable to determine quarterly EPS growth.")
            growth = None
        return growth
    
    
    def getEpsGrowthAnnual(self, a1, a2):
        """Calculates the EPS growth (%) for year a1 compared to a2.
        
        The EPS growth is calculated as the ratio EPS(a1)/EPS(a2) * 100%.
        """
        epsY1 = self.getEpsAnnual(a1)
        epsY2 = self.getEpsAnnual(a2)
        try:
            growth = (epsY1 / epsY2) * 100.
        except:
            print("Unable to determine quarterly EPS growth.")
            growth = None
        return growth
        
        
    def __slope(self, xf, xi, yf, yi):
        """Calculates the slope as (yf-yi)/(xf-xi)."""
        if (xf - xi) == 0.0:
            return 0.0

        return float((yf - yi) / (xf - xi))
    
    
    def getStabilityOfEpsGrowth(self, numQuarters):
        """Calculates the stability of the quarterly EPS growth over the last numQuarters (<20).
        
        The stability is calculated as the amount of deviation from the best-fit-line growth. 
        In other words, a line is fitted through the data, and the goodness-of-fit is determined.
        """
        if numQuarters < 20:
            x = []
            y = []
            firstDate = None
            try:
                firstDate = self.all10QFilings[self._getQuarter(0)].getReportDate()
            except:
                ## If the 10-Q for the current quarter is missing, there should be a 10-K instead
                firstDate = self.all10KFilings[self._getYear(0)].getReportDate()
            ## create the arrays of EPS vs nDays (from most recent filing) values
            for i in range(0, -numQuarters, -1):
                qKey = self._getQuarter(i)
                y.append(self.getEpsQuarter(i))
                try:
                    x.append((firstDate - self.all10QFilings[qKey].getReportDate()).days)
                except:
                    ## Locate the 10-K submitted instead of the 10-Q
                    diff = int(qKey[:4]) - int(self.currentY[1:])
                    x.append((firstDate - self.all10KFilings[self._getYear(diff)].getReportDate()).days)
            ## Fit a polynomial of degree 1 through the data: bx + c. Then compute the goodness-of-fit.
            p = polyfit(x, y, 1)
            yfit = polyval(p, x)
            sigma = (y - yfit) / y
            error = sigma * sigma
            res = error.sum()
            return res
        return None
    
    
    def getEpsGrowthAcceleration(self, numQuarters):
        """Returns the (mean) acceleration of EPS growth over the specified number of quarters.
        
        The acceleration is calculated as the second derivative of the data. numQuarters is required to 
        be between 2 and 15. At least three quarters are necessary to calculate acceleration.
        """
        if numQuarters < 20:
            x = []
            y = []
            firstDate = None
            try:
                firstDate = self.all10QFilings[self._getQuarter(0)].getReportDate()
            except:
                ## If the 10-Q for the current quarter is missing, there should be a 10-K instead
                firstDate = self.all10KFilings[self._getYear(0)].getReportDate()
            ## create the arrays of EPS vs nDays (from most recent filing) values
            for i in range(0, -numQuarters, -1):
                qKey = self._getQuarter(i)
                y.append(self.getEpsQuarter(i))
                try:
                    x.append((firstDate - self.all10QFilings[qKey].getReportDate()).days)
                except:
                    ## Locate the 10-K submitted instead of the 10-Q
                    diff = int(qKey[:4]) - int(self.currentY[1:])
                    x.append((firstDate - self.all10KFilings[self._getYear(diff)].getReportDate()).days)
            ## Fit a polynomial of degree 2 through the data: ax**2 + bx + c. 'a' should be the acceleration
            p = polyfit(x, y, 2)
            return p[0]
        return None
    
    
    def getSalesGrowth(self, q1, q2):
        """Calculates the Sales growth (%) for quarter q1 compared to q2.
        
        The Sales growth is calculated as the ratio Sales(q1)/Sales(q2) * 100%.
        """
        salesQ1 = self.getSalesQuarter(q1)
        salesQ2 = self.getSalesQuarter(q2)
        try:
            growth = (salesQ1 / salesQ2) * 100.
        except:
            print("Unable to determine quarterly Sales growth.")
            growth = None
        return growth
    
    
    def getSalesGrowthAcceleration(self, numQuarters):
        """Returns the (mean) acceleration of Sales growth over the specified number of quarters.
        
        The acceleration is calculated as the second derivative of the data. numQuarters is required to 
        be between 2 and 15. At least three quarters are necessary to calculate acceleration.
        """
        if numQuarters < 20:
            x = []
            y = []
            firstDate = None
            try:
                firstDate = self.all10QFilings[self._getQuarter(0)].getReportDate()
            except:
                ## If the 10-Q for the current quarter is missing, there should be a 10-K instead
                firstDate = self.all10KFilings[self._getYear(0)].getReportDate()
            ## create the arrays of EPS vs nDays (from most recent filing) values
            for i in range(0, -numQuarters, -1):
                qKey = self._getQuarter(i)
                y.append(self.getSalesQuarter(i))
                try:
                    x.append((firstDate - self.all10QFilings[qKey].getReportDate()).days)
                except:
                    ## Locate the 10-K submitted instead of the 10-Q
                    diff = int(qKey[:4]) - int(self.currentY[1:])
                    x.append((firstDate - self.all10KFilings[self._getYear(diff)].getReportDate()).days)
            ## Fit a polynomial of degree 2 through the data: ax**2 + bx + c. 'a' should be the acceleration
            p = polyfit(x, y, 2)
            return p[0]
        return None
    
    
    def logErrors(self):
        with open("{:s}_log.txt".format(self.ticker)) as f:
            for item in self.all10QFilings:
                f.write("\n{:s}:\n".format(item))
                f.write(self.all10QFilings[item].printErrors())
            for item in self.all10KFilings:
                f.write("\n{:s}:\n".format(item))
                f.write(self.all10KFilings[item].printErrors())
                
                
    def plotEpsQuarter(self):
        """Generates a log-plot of quarterly EPS data."""
        pass
    
    def plotStockData(self):
        """Generates a plot of the weekly stock data for the last three years."""
        pass
    
    def getStockData(self):
        """Download the weekly stock data for the last three years from somehwere."""
        pass
    
    def getStockGrowth(self):
        """Returns the stock growth as the slope of the best-fit line through the stock data."""
        pass
    
    def getStockAcceleration(self):
        """Fits the equation a*x^2+b*x+c through the data and returns the 'a' coefficient."""
        pass
    
    ## Lofty future goal: write algorithm(s) that identifies Canslim patterns in the stock data
        