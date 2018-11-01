import pandas
from sqlalchemy import create_engine

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
	
	
NvdaCanslimParams= CanslimParams("NVDA", all_10Qs, all_10Ks)
NvdaCanslimParams.loadData()
NvdaCanslimParams.getEpsQuarter(0)
NvdaCanslimParams.getEpsAnnual(-1)
NvdaCanslimParams.getSalesQuarter(-2)
NvdaCanslimParams.getSalesAnnual(-2)
NvdaCanslimParams.getRoeCurrent()
NvdaCanslimParams.getEpsGrowthQuarter(-3, -4)
NvdaCanslimParams.getEpsGrowthAnnual(0, -1)
NvdaCanslimParams.getStabilityOfEpsGrowth(4)
NvdaCanslimParams.getEpsGrowthAcceleration(4)