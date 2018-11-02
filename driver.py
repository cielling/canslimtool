import pandas
from sqlalchemy import create_engine
from bs4 import BeautifulSoup as BSoup

from CanslimParams import CanslimParams

## Update the idx and cik_ticker_name tables in the database

## Read in the screener_results.xls file

## Do the Canslim analysis for each ticker in that file

## Keep track of tickers that gave an error

## Write the analysis results to a file screener_results_analysis.xls



## Eventually: make plots



ticker= "NVDA"

## Open the database of index file names to generate url
## Note: Loading this database takes a long time! Do this once, and pass the cik_ticker_name 
## dataframe to the CanslimParams class
engine = create_engine('sqlite:///edgar_idx.db')
with engine.connect() as conn, conn.begin():
    #load the table with the index files info
    ## Ensure that the 'date' column is parsed as a datetime format
    idx = pandas.read_sql_table('idx', conn, parse_dates= {'date': "%Y-%m-%d"})
    #load the look-up table for ticker symbol to CIK translation
    cik_ticker_name = pandas.read_sql_table ('cik_ticker_name', conn)
    #handle the case where there are multiple stocks with the same ticker; just select the first?!?
    cik =((cik_ticker_name.cik[cik_ticker_name.ticker == ticker]))
    print ((cik.iloc[0]))
    all_links = idx[idx.cik == cik.iloc[0]]
    all_10Qs = all_links[all_links.type == '10-Q']
    #verify that this gets the amended 10-Q's
    #all_10Qs.append (all_links[all_links.type == '10-Q\A'])
    all_10Ks = all_links[all_links.type == '10-K']
    print (all_10Qs, all_10Ks)
	
	

Canslim = {}
Canslim['Eps_current_Q_per_same_Q_prior_year'] = -99
Canslim['Sales_current_Q_per_prior_Q'] = -99
Canslim['Sales_growth_accel_last_3_Q'] = -99
Canslim['Eps_growth_accel_last_3_Q'] = -99
Canslim['Stability_of_Q_eps_growth_last_3_years'] = -99
Canslim['Excellency_of_eps_increase'] = -99
Canslim['Num_Q_with_eps_growth_deceleration'] = -99
Canslim['Num_years_annual_eps_increasing_last_3_years'] = -99