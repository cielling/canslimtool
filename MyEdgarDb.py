def get_list_sec_filings ():
    """Generate the list of index files archived in EDGAR since start_year (earliest: 1993) until the most recent quarter
       Note: this does not download the filings itself, just enough information to generate the filing urls from it.
    """
    import datetime

    current_year = datetime.date.today().year
    current_quarter = (datetime.date.today().month - 1) // 3 + 1
    # go back the last four years so we get the last ten 10-Q's and last three 10-K's
    start_year = current_year - 5
    with open("logfile.txt", "a+") as logfile:
        logfile.write('Start year for downloading SEC data is {:d}'.format(start_year))
    ## Generate a list of quarter-year combinations for which to get urls
    years = list(range(start_year, current_year))
    quarters = ['QTR1', 'QTR2', 'QTR3', 'QTR4']
    history = [(y, q) for y in years for q in quarters]
    for i in range(1, current_quarter + 1):
        history.append((current_year, 'QTR%d' % i))
    urls = ['https://www.sec.gov/Archives/edgar/full-index/%d/%s/master.idx' % (x[0], x[1]) for x in history]
    urls.sort()
    ## Update the database with these urls
    update_index_files_db (urls)
    #return urls
    
def update_index_files_db (urls):
    """Download index files and write content into SQLite."""
    import sqlite3
    import requests

    con = sqlite3.connect('edgar_idx.db')
    cur = con.cursor()
    # to do: check if table exists, if yes, then update, don't erase
    cur.execute('DROP TABLE IF EXISTS idx')
    cur.execute('CREATE TABLE IF NOT EXISTS idx (cik TEXT, conm TEXT, type TEXT, date TEXT, path TEXT)')
    
    updaterecords = tuple()

    with open("logfile.txt", "w") as logfile:
        for url in urls:
            #to do: how exactly does this work? modify to only download missing entries
            #get the data located at this url
            lines = requests.get(url).text.splitlines()
            #parse the data into sec filings type and remote path (and some other info)
            records = [tuple(line.split('|')) for line in lines[11:]]
            #put this into the database (to be downloaded later)
            cur.executemany('INSERT INTO idx VALUES (?, ?, ?, ?, ?)', records)
            logfile.write('{:s} - downloaded info and wrote to SQLite DB\n'.format(url))

    con.commit()
    con.close()
   
def get_cik_ticker_lookup_db ():
    """This creates the look-up table to translate ticker symbol to CIK identifier. 
    WARNING! This destroys the existing table!"""
    import sqlite3
    from sqlalchemy import create_engine
    import pandas as pd

    #read in the cik-ticker-company name lookup table
    df = pd.read_csv ("cik_ticker.csv", sep='|')
    #print (df.columns)
    #select only the columns we need
    lookup_table_df = df.loc[:, ['CIK', 'Ticker', 'Name']]
    #print (lookup_table_df.CIK.size)

    #write this as a second table in edgar_idx
    con = sqlite3.connect('edgar_idx.db')
    cur = con.cursor()
    cur.execute('DROP TABLE IF EXISTS cik_ticker_name')
    cur.execute('CREATE TABLE cik_ticker_name (cik TEXT, ticker TEXT, name TEXT)')

    #loop over dataframe, and collect the data to insert
    counter = 0
    records = []
    for i in range (0, lookup_table_df.CIK.size):
        records.append (("{}".format (lookup_table_df.CIK.iloc[i]), 
                   "{}".format (lookup_table_df.Ticker.iloc[i]), 
                   "{}".format (lookup_table_df.Name.iloc[i]))
                       )
        counter += 1
    #print (records)
    #insert data into the table
    cur.executemany ('INSERT INTO cik_ticker_name VALUES (?, ?, ?)', records)

    con.commit ()
    con.close ()
