import requests
from bs4 import BeautifulSoup as BSoup
import pandas as pd
import csv
import requests
import os
from datetime import datetime, timedelta
from SecFiling import SecFiling
import traceback

class SecFiling10Q(SecFiling):
        
    def getEps(self):
        """Retrieve the current EPS from the filing."""
        all_eps_tags = []
        try:
            for tag in self.all_tags:
                if 'us-gaap:earningspersharebasic' in tag.name:
                    all_eps_tags.append(tag)
            self.currentEps = self.getCurrentValue(all_eps_tags)
        except:
            self.errorLog.append("Unable to find the EPS information in the filing.")
            return None
        return self.currentEps
                    
    
    def getSales(self, contextId = ""):
        """Retrieves the current Sales data from the filing.
        
        WARNING! The 'currentContextRef' member must have been set first (e.g. by calling getEps or getRoe 
        before calling this function) for this function to work properly. It seems to be very tricky to 
        figure out the currentContextRef by itself."""
        if not contextId:
            if not self.currentContextId:
                self.errorLog.append("ERROR! current contextId is not set!")
                return -99.0
            else:
                contextId = self.currentContextId
        all_sales_tags = []
        try:
            for tag in self.all_tags:
                ## The filings seem to use either 'Revenues' or 'SalesRevenuesNet' to indicate the net sales amount
                ## But the 'Revenues' tag also contains other stuff, need to filter it by its contextref attribute
                if 'us-gaap:Revenues'.lower() == tag.name.strip():
                    if (tag.attrs)['contextref'] == contextId:
                        all_sales_tags.append(tag)
                elif 'us-gaap:SalesRevenuesNet'.lower() == tag.name.strip():
                    if (tag.attrs)['contextref'] == contextId:
                        all_sales_tags.append(tag)
                ## Some of AAPL's statements use this tag:
                elif 'us-gaap:salesrevenuenet'.lower() == tag.name.strip():
                    if (tag.attrs)['contextref'] == contextId:
                        all_sales_tags.append(tag)
        except BaseException as be:
            self.errorLog.append("Unable to find Sales data in filing.")
            self.errorLog.append(be)
            return None
        self.currentSales = self.getCurrentValue(all_sales_tags) 
        return self.currentSales
    
    
    def getRoe(self):
        """Retrieves the current Return on Equity from the filing."""
        ## First find the stockholders' equity
        all_se_tags = []
        ## Then find the net income
        all_ni_tags = []
        self.currentSE = None
        self.currentNI = None
        try:
            for tag in self.all_tags:
                if 'us-gaap:StockholdersEquity'.lower() == tag.name.strip():
                    all_se_tags.append(tag)
                if 'us-gaap:NetIncomeLoss'.lower() == tag.name.strip():
                    all_ni_tags.append(tag)
            self.currentSE = self.getCurrentValue(all_se_tags)
            self.currentNI = self.getCurrentValue(all_ni_tags)
        except:
            if not self.currentSE:
                self.errorLog.append("Unable to find Stockholders' Equity in filing.")
            if not self.currentNI:
                self.errorLog.append("Unable to find Net Income in filing.")
            return None
        ## Return on equity = net income / stockholders' equity
        self.currentRoe = 0.0
        if self.currentSE and self.currentSE > 0.0:
            self.currentRoe = self.currentNI / self.currentSE
        return self.currentRoe
      
    
    def getCurrentValue(self, tagList):
        """Finds the tag for the current date from a list of tags, and returns its value."""
        prevDiff = timedelta(9999, 0, 0) ## days, seconds, microseconds (!)
        prevContextRefLen = 100000
        current = None
        try:
            for tag in tagList:
                ## Find the quarter that ended closest to the reportDate, make sure it's a quarter
                ## TODO: figure out how to do this for the 10-K's
                contextRef = str((tag.attrs)['contextref'])
                ## The various 'us-gaap:<quantity-of-interest>' tags can occur multiple times for the same time frame,
                ## but usually distinguish between contextRef names (i.e. the contextref attributes are different, but 
                ## denote the same time frame). It seems that I generally want the contextRef with the shortest name
                ## (i.e. least special one)?
                contextRefLen = len(contextRef)
                if contextRef in self.contextIds:
                    tag_dates = self.contextIds[contextRef]
                else:
                    tag_dates = self.getStartEndDateForContext(contextRef)
                    self.contextIds[contextRef] = tag_dates
                try:
                    diff = self.reportDate - tag_dates[1]
                    ## Find the closest enddate to the ReportDate, i.e. the 'current' date
                    if abs(diff.days) < abs(prevDiff.days): ## found a date closer to the reportDate
                        prevDiff = diff
                        ## Reset the length of the contextref string
                        prevContextRefLen = 100000
                    ## found another candidate, do all the checks
                    if abs(diff.days) <= abs(prevDiff.days): ## found a date closer to the reportDate 
                        ## If the date is an instantaneous date, only look at the 'diff'
                        if tag_dates[1] == tag_dates[0]:
                            if contextRefLen < prevContextRefLen:
                                prevContextRefLen = contextRefLen
                                current = tag
                                prevDiff = diff
                        ## If a date range is given, make sure it's about a year long
                        elif abs((tag_dates[1] - tag_dates[0]).days - 91) < 5:
                            if contextRefLen < prevContextRefLen:
                                prevContextRefLen = contextRefLen
                                current = tag
                                prevDiff = diff
                except BaseException as be:
                    self.errorLog.append(be)
                    return None
            if current:
                self.currentContextId = (current.attrs)['contextref']
            else:
                self.errorLog.append("Failed to determine the value for current contextId:")
                self.errorLog.append("Received tagList: \n" + str(tagList))
                self.errorLog.append("Stored contextIds: \n" + str(self.contextIds))
                return None
        except Exception as ex:
            self.errorLog.append("Unable to determine the current value:")
            self.errorLog.append(type(ex).__name__)
            self.errorLog.append(ex)
            traceback.print_exc()
            return None
        return float(current.text)  
    

