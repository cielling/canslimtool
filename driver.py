import pandas as pd
#from sqlalchemy import create_engine
import sqlite3
from bs4 import BeautifulSoup as BSoup
from datetime import datetime
import os
from sys import argv

from MyEdgarDb import get_list_sec_filings, get_cik_ticker_lookup_db, lookup_cik_ticker
from CanslimParams import CanslimParams


def analyzeTicker(df, doRestart, procNum = 0):
    ## See if a previous analysis-log exists. If it does, assume this is a restart
    ## from it. If not, do a new analysis run.
    newRun = not doRestart
    if newRun:
        mode = "w"
    else:
        mode = "r+"
        
    ## Load the database of index file names to generate url
    with sqlite3.connect('edgar_idx.db') as conn:
        cursor = conn.cursor()
        with open("analysislog"+str(procNum)+".txt", mode) as logfile:
            with open("analysiserrors"+str(procNum)+".txt", mode) as errorlog:
                ## Keep a log of all the files that were processed. 
                ## Do the Canslim analysis for each ticker in that file
                ## Keep track of tickers that gave an error
                symbol = df.Symbol.iloc[1]
                print("Processing {:s}\n".format(symbol))
                logfile.write("Processing {:s}\n".format(symbol))                    
                # ## Add/reset the columns we're going to fill out:
                df['Eps_current_Q_per_same_Q_prior_year'] = -99.99
                df['Eps_previous_Q_per_same_Q_prior_year'] = -99.99
                df['Num_years_annual_eps_increasing_last_3_years'] = -99.99
                df['Annual_eps_growth_Y0_Y1'] = -99.99
                df['Annual_eps_growth_Y1_Y2'] = -99.99
                df['Annual_eps_growth_Y2_Y3'] = -99.99
                df['Excellency_of_eps_increase'] = -99.99
                df['Eps_growth_accel_last_3_Q'] = -99.99
                df['Num_Q_with_eps_growth_deceleration'] = -99.99
                df['Current_roe'] = -99.99
                df['Stability_of_eps_growth_last_16_Q'] = -99.99
                df['Eps_growth_accel_last_10_Q'] = -99.99
                df['Sales_current_Q_per_prior_Q'] = -99.99
                df['Sales_growth_accel_last_3_Q'] = -99.99
                ## Get the 10-K and 10-Q filing references from the database
                ## First, look up the CIK for the ticker symbol
                cursor.execute('''SELECT * FROM cik_ticker_name WHERE ticker=?;''',(symbol,))
                res = cursor.fetchall()
                ## If this ticker is not in the lookup database, try to search on the web.
                if not res:
                    record = lookup_cik_ticker(symbol)
                    if not record:
                        print("Unsuccessful.")
                        return df
                    #insert data into the table
                    #cursor.execute ('INSERT INTO cik_ticker_name VALUES (?, ?, ?)', record)
                    #conn.commit ()
                    cik = record[0]
                    print(cik)
                else:
                    try: 
                        cik = res[0][0]
                    except BaseException as be:
                        errorlog.write("Unable to locate CIK for ticker {:s}.".format(symbol))
                        errorlog.write("Record in database: {:s}".format(str(res)))
                        errorlog.write(str(be))
                        return df
                ## Then pull out the corresponding data
                cursor.execute('''SELECT * FROM idx WHERE cik=?;''', (cik,))
                recs = cursor.fetchall()
                ## Create a list of column names from the database column names
                names = list(map(lambda x: x[0], cursor.description))
                idx = pd.DataFrame(data=recs, columns=names)
                ## Ensure that the 'date' column is formatted as a time stamp
                idx['date'] = pd.to_datetime(idx['date'])
                ## Remove any funny symbols in the columns. Apparently has to be done one-by-one.
                for i in idx.index:
                    idx.loc[i,'conm'] = idx.loc[i,'conm'].replace("/", "") 
                all_10Qs = idx[idx.type == '10-Q']
                #verify that this gets the amended 10-Q's
                #all_filings.append (all_links[all_links.type == '10-Q\A'])
                all_10Ks = idx[idx.type == '10-K']
                canslim = CanslimParams(symbol, all_10Qs, all_10Ks)
                if (canslim.loadData()):
                    ## Do the Canslim analysis. Remember to calculate the EPS(q) before calculating the 
                    ## Sales(q) until the contextId-issue is fixed.
                    
                    ## For the excellency of the EPS growth, determine the following two factors:
                    ## Two current quarters EPS as compared to the same quarters last year.
                    epsGrowth1 = canslim.getEpsGrowthQuarter(0, -4)
                    epsGrowth2 = canslim.getEpsGrowthQuarter(-1, -5)
                    count = 0
                    if epsGrowth1:
                        df.loc[symbolIdx, 'Eps_current_Q_per_same_Q_prior_year'] = epsGrowth1
                        if epsGrowth1 > 0:
                            count += 1
                    if epsGrowth2:
                        df.loc[symbolIdx, 'Eps_previous_Q_per_same_Q_prior_year'] = epsGrowth2
                        if epsGrowth2 > 0:
                            count += 1
                    if epsGrowth1 and epsGrowth2:
                        if epsGrowth1 > epsGrowth2:
                            count += 1
                    ## The number of years that the annual EPS increased over the last three years, and the annual growth.
                    growth1 = canslim.getEpsGrowthAnnual(0, -1)
                    growth2 = canslim.getEpsGrowthAnnual(-1, -2)
                    growth3 = canslim.getEpsGrowthAnnual(-2, -3)
                    numYears = 0
                    if growth1:
                        df.loc[symbolIdx, 'Annual_eps_growth_Y0_Y1'] = growth1
                        if growth1 > 0.0:
                            numYears += 1
                    if growth2:
                        df.loc[symbolIdx, 'Annual_eps_growth_Y1_Y2'] = growth2
                        if growth2 > 0.0:
                            numYears += 1
                    if growth3:
                        df.loc[symbolIdx, 'Annual_eps_growth_Y2_Y3'] = growth3
                        if growth3 > 0.0:
                            numYears += 1
                    df.loc[symbolIdx, 'Num_years_annual_eps_increasing_last_3_years'] = numYears
                    if (growth1) and (growth2) and (growth3):
                        if growth1 > growth2:
                            count += 1
                        if growth2 > growth3:
                            count += 1
                        count + numYears
                    df.loc[symbolIdx, 'Excellency_of_eps_increase'] = count
                        
                    ## Calculate the acceleration of EPS growth for the last three quarters
                    epsAcc = canslim.getEpsGrowthAcceleration(3)
                    try:
                        if epsAcc.all():
                            df.loc[symbolIdx, 'Eps_growth_accel_last_3_Q'] = epsAcc[0]
                    except:
                        pass
                        
                    ## Check if there are two consecutive quarters with EPS deceleration
                    totalDecel = 0
                    consecutiveDecel = 0
                    err = False
                    for i in range(0, 10):
                        start = 0 - i
                        end = -1 - i
                        rate = canslim.getEpsGrowthRateQuarter(end, start)
                        if not rate:
                            err = True
                            break
                        if i == 0:
                            prev = rate
                        else:
                            if rate < prev: ## deceleration
                                consecutiveDecel += 1
                                if consecutiveDecel < totalDecel:
                                    totalDecel = consecutiveDecel
                            else:
                                consecutiveDecel = 0
                    if not err:
                        df.loc[symbolIdx, 'Num_Q_with_eps_growth_deceleration'] = totalDecel
                        
                    ## Calculate the ROE of the current quarter
                    roe = canslim.getRoeCurrent()
                    if roe:
                        df.loc[symbolIdx, 'Current_roe'] = roe
                        
                    ## Calculate the stability (goodness-of-fit) for the EPS growth over the last 16 quarters
                    stability = canslim.getStabilityOfEpsGrowth(16)
                    if stability:
                        df.loc[symbolIdx, 'Stability_of_eps_growth_last_16_Q'] = stability
                        
                    ## Calculate the EPS growth acceleration over the last 10 quarters
                    epsAcc2 = canslim.getEpsGrowthAcceleration(10)
                    try:
                        df.loc[symbolIdx, 'Eps_growth_accel_last_10_Q'] = epsAcc2[0]
                    except:
                        pass
                        
                    ## At this point, all contextIds needed for Sales should be set
                    ## Get Sales(current Q)/Sales(same Q prior year), as %
                    salesGrowth = canslim.getSalesGrowthQuarter(0, -4)
                    if salesGrowth:
                        df.loc[symbolIdx, 'Sales_current_Q_per_prior_Q'] = salesGrowth
                        
                    ## Calculate the acceleration of Sales growth for the last three quarters
                    salesAcc = canslim.getSalesGrowthAcceleration(3)
                    try:
                        df.loc[symbolIdx, 'Sales_growth_accel_last_3_Q'] = salesAcc[0]
                    except BaseException as be:
                        pass

                    canslim.logErrors()
                    del canslim
                    print("Successfully analyzed filings for ticker {:s}".format(symbol))
                else:
                    errorlog.write("Unable to open filings for {:s}\n".format(symbol))
                    del canslim

                return df
                    
                    
## TODO: (some) foreign companies submit a 20-F instead of a 10-K
runOnce = False
if "runonce" in argv:
    runOnce = True
    
## Tell the analysis to do a restart 
doRestart = False
if ("--r" in argv) or ("restart" in argv):
    doRestart = True    

tStart = datetime.now()

## Update the idx and cik_ticker_name tables in the database
print("Updating master index.")
#get_list_sec_filings ()
print("Updating CIK-ticker lookup table.")
#get_cik_ticker_lookup_db ()

    
## Read in the screener_results.xls file
### REMEMBER TO REMOVE TRAILING JUNK FROM SCREENER_RESULTS.XLS FIRST!!! ###
screenerResultsFile = "screener_results.xls"
df = pd.read_excel (screenerResultsFile, header = 0)
screenerResultsFileAnalysed = "screener_results_analysis.xls"
dfAnalysed = pd.DataFrame()
## Guarantee that the spreadsheet is sorted alphabetically by ticker symbol, and that the index
## is monotonically increasing.
## Note, the sort order seems to not be persistent, so abandon this idea.
#df.sort_values('Symbol', inplace = True)
#df.reset_index(drop = True)
print(df.size)

logfile = open("analysislog.txt", "r+")
analyzed = logfile.read().splitlines()
logfile.close()
for symbol in df.Symbol:
    ## Skip symbols I've already analyzed.
    if symbol in analyzed:
        print("Skipping {:s}".format(symbol))
        continue
    dfAnalyzedTicker = analyzeTicker(df, doRestart=True)
    dfAnalyzed.append(dfAnalyzedTicker)
    dfAnalyzed.to_excel(screenerResultsFileAnalysed, index=None)
    break

tEnd = datetime.now()
print("Runtime was {:d} sec.".format((tEnd - tStart).seconds))
## Eventually: make plots


#################### Code Graveyard #######################
# Check if there 
                # ## are any tickers that were already processed and can be skipped.
                # ## If there are no records in the analysis-log file, treat this as a new run.
                # ## Force doing new stars
                # #newRun = True
                # if not newRun:
                    # processed = logfile.readlines()
                # if newRun:
                    # ## Add the columns we're going to fill out:
                    # df['Eps_current_Q_per_same_Q_prior_year'] = -99.99
                    # df['Eps_previous_Q_per_same_Q_prior_year'] = -99.99
                    # df['Num_years_annual_eps_increasing_last_3_years'] = -99.99
                    # df['Annual_eps_growth_Y0_Y1'] = -99.99
                    # df['Annual_eps_growth_Y1_Y2'] = -99.99
                    # df['Annual_eps_growth_Y2_Y3'] = -99.99
                    # df['Excellency_of_eps_increase'] = -99.99
                    # df['Eps_growth_accel_last_3_Q'] = -99.99
                    # df['Num_Q_with_eps_growth_deceleration'] = -99.99
                    # df['Current_roe'] = -99.99
                    # df['Stability_of_eps_growth_last_16_Q'] = -99.99
                    # df['Eps_growth_accel_last_10_Q'] = -99.99
                    # df['Sales_current_Q_per_prior_Q'] = -99.99
                    # df['Sales_growth_accel_last_3_Q'] = -99.99
                    # dfAnalysed = pd.DataFrame()
                # else:
                    # lastTicker = processed[-1].split(" ")[1].strip()
                    # print("Starting from ticker {:s}".format(lastTicker))
                    # ## Re-process the last ticker, in case it was interrupted and didn't finish.
                    # nextLine = df[df.Symbol == lastTicker]
                    # nextIndex = nextLine.index[0]
                    # print("Starting at index {}".format(nextIndex))
                    # ## Open already analysed file, and append to it.
                    # dfAnalysed = pd.read_excel("screener_results_analysis"+str(procNum)+".xls", header = 0)