import requests
from bs4 import BeautifulSoup as BSoup
import pandas as pd
import csv
import requests
import os
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import traceback

class SecFiling(ABC):
    """Holds the data of a generic SEC filing.
    
    Expected to be subclassed by 'SecFiling10K' and 'SecFiling10Q'. Also expected to be a utility to CanslimParams, i.e.
    driven by it.
    
    Before running this, make sure my edgar_idx.db is up-to-date. analyze_stockdata.get_list_sec_filings() will 
    update the 'idx' table (i.e. the database with the relevant urls), and analyze_stockdata.get_cik_ticker_lookup_db()
    will update the lookup table for CIK number - ticker symbol correlation.
    """
    def __init__(self, ticker):
        self.ticker = ticker
        self.xbrlInstance = None
        self.contextIds = {}
        self.currentContextId = ""
        self.errorLog = []
        self.currentSE = None
        self.currentNI = None
        self.reportDate = None
        
        
    def __del__(self):
        self.contextIds.clear()
        del self.errorLog[:]
        
    
    def getReportDate(self):
        return self.reportDate
        
        
    def download(self, cik, co_name, filing_type, filing_date, filing_link, downloadPath = "SECDATA"):
        """Retrieves a SEC filing from EDGAR. Follow by a call to 'load()'.
        
        Also a roundabout way of getting the filename for this data file.
        """
        # inspired by http://kaikaichen.com/?p=681
        saveas = '_'.join([cik, co_name, filing_type, str(filing_date)])
        saveDir = os.path.join(downloadPath, co_name)
        self.fname = os.path.join (saveDir, saveas)
        ## Only download if the file doesn't exist yet (at the expected path)
        if not os.path.exists(self.fname):
            url = 'https://www.sec.gov/Archives/' + filing_link.strip()
            if not os.path.exists(saveDir):
                os.makedirs(saveDir)
            with open("logfile.txt", "a+") as logfile:
                with open(self.fname, 'wb') as f:
                    f.write(requests.get('%s' % url).content)
                    logfile.write('{:s} - downloaded and saved as {:s}\n'.format(url, self.fname))
        return (self.fname)
    
    
    def load(self, fname):
        """Loads the data of SEC filing."""
        f = open (fname, "r")
        ## TODO: Do I need to have the whole file in memory?
        wholeFile = f.read ()
        f.close ()
        soup = BSoup (wholeFile, "lxml")
        ## Extract some basic info from the SEC-header section
        sec_header = soup.find("sec-header")
        try:
            for l in sec_header.text.split("\n"):
                if 'conformed period of report' in l.lower():
                    self.reportDate = datetime.strptime((l.split(":")[1]).strip(), "%Y%m%d")
                if 'standard industrial classification' in l.lower():
                    self.stdIndustrialClass = l.split(":")[1].strip()
            print("Report date: {:s}, industrial class: {:s}". format(str(self.reportDate), self.stdIndustrialClass))
        except:
            self.errorLog.append("Unable to find SEC-header in file.")
            return False
        
        ## Find the XBRL Instance document. It has the description-tag "XBRL INSTANCE DOCUMENT" within its document-tag.
        doc_tag = soup.find_all("document")
        try:
            for tag in doc_tag:
                description = tag.find("description").get_text().lower()
                if (description.startswith("xbrl instance document")):
                    self.xbrlInstance = tag
                    break
        except:
            self.errorLog.append("Unable to find document-tags in file.")
            return False
        
        if not self.xbrlInstance:
            self.errorLog.append("ERROR: unable to find Instance document for {:s}".format(self.fname))
            return False
        
        ## 'findAll('us-gaap:earningspersharebasic')' doesn't seem to work... so find them manually
        self.all_tags = self.xbrlInstance.findAll()
        if not self.all_tags:
            self.errorLog.append("No tags found!")
            return False
        return True
    
    
    def save(self):
        """Saves the data to file."""
        pass
     
        
    @abstractmethod
    def getEps(self):
        """Retrieve the current EPS from the filing."""
        ## 'findAll('us-gaap:earningspersharebasic')' doesn't seem to work... so find them manually
        pass
            
        
    @abstractmethod
    def getSales(self):
        """Retrieves the current Sales data from the filing.
        
        WARNING! The 'currentContextRef' member must have been set first (e.g. by calling getEps or getRoe 
        before calling this function) for this function to work properly. It seems to be very tricky to 
        figure out the currentContextRef by itself."""
        pass
        
        
    @abstractmethod
    def getRoe(self):
        """Retrieves the current Return on Equity from the filing."""
        pass
        
    @abstractmethod
    def getCurrentValue(self, tagList):
        pass
    
        
    def getStockholdersEquity(self):
        """Returns the value saved in self.currentSE.
        
        This attribute is populated by getRoe(). It is 'None' until that function is called. 
        Useful for debugging purposes. 
        """
        return self.currentSE
    
    
    def getNetIncome(self):
        """Returns the value saved in self.currentNI.
        
        This attribute is populated by getRoe(). It is 'None' until that function is called. 
        Useful for debugging purposes. 
        """
        return self.currentNI
            
    def getStartEndDateForContext(self, contextRef):
        """Looks up the date for the given contextref/id.

        This used to be a method under the SecFiling class. For some reason (me, Jupyter notebooks, other), 
        I would get an AttributeError that SecFiling10Q did not have this attribute when calling, e.g. 'getEps()
        on a SecFiling10Q object. So I nested it here under 'getCurrentValue'. """
        ## Some filings use 'xbrli:context' as the tag
        periodXml = self.xbrlInstance.find("xbrli:context", {"id" : contextRef})
        ## Some filings just use 'context' as the tag
        if not periodXml:
            periodXml = self.xbrlInstance.find("context", {"id" : contextRef})
        if periodXml:
            ## We found a context-tag, try to determine the dates. Again, some use 'xbrli:<tag>', some just
            ## use '<tag>'. Also, some contexts are instantaneous ('instant'), and some indicate a date range
            ## Search for each case, and search for all known variants of the tag names, just in case some
            ## filings mix between them.
            startdate = periodXml.find("xbrli:startdate") ## or just 'startdate'
            if not startdate:
                startdate = periodXml.find("startdate")
            enddate = periodXml.find("xbrli:enddate") ## or just 'enddate'
            if not enddate:
                enddate = periodXml.find("enddate")
            instant = periodXml.find("xbrli:instant") ## instantaneous date, not a date range
            if not instant:
                instant = periodXml.find("instant") ## instantaneous date, not a date range
            ## Presumably, there is either an 'instant' or a 'startdate' + 'enddate'
            if instant:
                startdate = instant
                enddate = startdate
        else:
            print("ERROR: Unable to find dates for contextref '{:s}'".format(contextRef))
            return None
        try:
            sd = datetime.strptime(startdate.text, "%Y-%m-%d")
        except:
            sd = None
        try:
            ed = datetime.strptime(enddate.text, "%Y-%m-%d")
        except:
            ed = None
        return [sd, ed]
        
        
    def getCurrentContextId(self):
        return self.currentContextId
        
        
    def printErrors(self):
        print("\n".join(e for e in self.errorLog))
            
