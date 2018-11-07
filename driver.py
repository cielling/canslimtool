import pandas as pd
from sqlalchemy import create_engine
from bs4 import BeautifulSoup as BSoup
from datetime import datetime

from MyEdgarDb import get_list_sec_filings, get_cik_ticker_lookup_db
from CanslimParams import CanslimParams

tStart = datetime.now()

## Update the idx and cik_ticker_name tables in the database
print("Updating master index.")
#get_list_sec_filings ()
print("Updating CIK-ticker lookup table.")
#get_cik_ticker_lookup_db ()

## Load the database of index file names to generate url
print("Loading edgar_idx.db. This could take a while.")
engine = create_engine('sqlite:///edgar_idx.db')
with engine.connect() as conn, conn.begin():
    #load the table with the index files info
    idx = pd.read_sql_table('idx', conn, parse_dates=['date'])
    #load the look-up table for ticker symbol to CIK translation
    cik_ticker_name = pd.read_sql_table ('cik_ticker_name', conn)

## Read in the screener_results.xls file
### REMEMBER TO REMOVE TRAILING JUNK FROM SCREENER_RESULTS.XLS FIRST!!! ###
df = pd.read_excel ("screener_results.xls", header = 0)

## Add the columns we're going to fill out:
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

with open("analysislog.txt", "w") as logfile:
    ## Do the Canslim analysis for each ticker in that file
    ## Keep track of tickers that gave an error
    for symbol in df.Symbol:
        ## Write the analysis from the previous iteration to a file screener_results_analysis.xls
        df.to_excel("screener_results_analysis.xls")
        print("Processing {:s}\n".format(symbol))
        logfile.write("Processing {:s}\n".format(symbol))
        ## Get the 10-K and 10-Q filing references from the database
        #handle the case where there are multiple stocks with the same ticker; just select the first?!?
        cik =((cik_ticker_name.cik[cik_ticker_name.ticker == symbol]))
        #print (type(cik.iloc[0]))
        all_links = idx[idx.cik == cik.iloc[0]]
        all_10Qs = all_links[all_links.type == '10-Q']
        #verify that this gets the amended 10-Q's
        #all_filings.append (all_links[all_links.type == '10-Q\A'])
        all_10Ks = all_links[all_links.type == '10-K']
        canslim = CanslimParams(symbol, all_10Qs, all_10Ks)
        if (canslim.loadData()):
            ## Do the Canslim analysis. Remember to calculate the EPS(q) before calculating the 
            ## Sales(q) until the contextId-issue is fixed.
            
            ## For the excellency of the EPS growth, determine the following two factors:
            ## Two current quarters EPS as compared to the same quarters last year.
            epsGrowth1 = canslim.getEpsGrowthQuarter(0, -4)
            epsGrowth2 = canslim.getEpsGrowthQuarter(-1, -5)
            if not epsGrowth1 or not epsGrowth2:
                canslim.logErrors()
                del canslim
                continue
            else:
                df.loc['Eps_current_Q_per_same_Q_prior_year', symbol] = epsGrowth1
                df.loc['Eps_previous_Q_per_same_Q_prior_year', symbol] = epsGrowth2
            ## The number of years that the annual EPS increased over the last three years, and the annual growth.
            growth1 = canslim.getEpsGrowthAnnual(0, -1)
            growth2 = canslim.getEpsGrowthAnnual(-1, -2)
            growth3 = canslim.getEpsGrowthAnnual(-2, -3)
            if not growth1 or not growth2 or not growth3:
                canslim.logErrors()
                del canslim
                continue
            else:
                numYears = 0
                if growth1 > 0.0:
                    numYears += 1
                if growth2 > 0.0:
                    numYears += 1
                if growth3 > 0.0:
                    numYears += 1
                df.loc['Num_years_annual_eps_increasing_last_3_years', symbol] = numYears
                df.loc['Annual_eps_growth_Y0_Y1', symbol] = growth1
                df.loc['Annual_eps_growth_Y1_Y2', symbol] = growth2
                df.loc['Annual_eps_growth_Y2_Y3', symbol] = growth3
                count = 0
                if epsGrowth1 > 0:
                    count += 1
                if epsGrowth2 > 0:
                    count += 1
                if epsGrowth1 > epsGrowth2:
                    count += 1
                if growth1 > growth2:
                    count += 1
                if growth2 > growth3:
                    count += 1
                count + numYears
                df.loc['Excellency_of_eps_increase', symbol] = count
                
            ## Calculate the acceleration of EPS growth for the last three quarters
            epsAcc = canslim.getEpsGrowthAcceleration(3)
            if not epsAcc.all():
                canslim.logErrors()
                del canslim
                continue
            else:
                df.loc['Eps_growth_accel_last_3_Q', symbol] = epsAcc[0]
                
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
            if err:
                canslim.logErrors()
                del canslim
                continue
            else:
                df.loc['Num_Q_with_eps_growth_deceleration', symbol] = totalDecel
                
            ## Calculate the ROE of the current quarter
            roe = canslim.getRoeCurrent()
            if not roe:
                canslim.logErrors()
                del canslim
                continue
            else:
                df.loc['Current_roe', symbol] = roe
                
            ## Calculate the stability (goodness-of-fit) for the EPS growth over the last 16 quarters
            stability = canslim.getStabilityOfEpsGrowth(16)
            if not stability:
                canslim.logErrors()
                del canslim
                continue
            else:
                df.loc['Stability_of_eps_growth_last_16_Q', symbol] = stability
                
            ## Calculate the EPS growth acceleration over the last 10 quarters
            epsAcc2 = canslim.getEpsGrowthAcceleration(10)
            if not epsAcc2.all():
                canslim.logErrors()
                del canslim
                continue
            else:
                df.loc['Eps_growth_accel_last_10_Q', symbol] = epsAcc2[0]
                
            ## At this point, all contextIds needed for Sales should be set
            ## Get Sales(current Q)/Sales(same Q prior year), as %
            salesGrowth = canslim.getSalesGrowthQuarter(0, -4)
            if not salesGrowth:
                canslim.logErrors()
                del canslim
                continue
            else:   
                df.loc['Sales_current_Q_per_prior_Q', symbol] = salesGrowth
                
            ## Calculate the acceleration of Sales growth for the last three quarters
            salesAcc = canslim.getSalesGrowthAcceleration(3)
            if not salesAcc.all():
                canslim.logErrors()
                del canslim
                continue
            else: 
                df.loc['Sales_growth_accel_last_3_Q', symbol] = salesAcc[0]

            print("Successfully analyzed filings for ticker {:s}".format(symbol))
            logfile.write("Successfully analyzed filings for ticker {:s}".format(symbol))
        else:
            logfile.write("Unable to open filings for {:s}".format(symbol))

tEnd = datetime.now()
print("Runtime was {:d} sec.".format((tEnd - tStart).seconds))
## Eventually: make plots
