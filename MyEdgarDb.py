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

    ## First, go to http://rankandfiled.com/#/data/tickers and download the current table 
    ## as CSV into this directory.

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
    ## Note that the CSV file does not include all tickers. Append these manually, and/or find a better way to handle this.
    records.append(("1577552", "BABA", "Alibaba Group Holding Ltd"))
    "0001024148", "BASFY", "BASF AKTIENGESELLSCHAFT"
    "0001161125","BCH", "Bank of Chile"
    "0001329099", "BIDU", "Baidu, Inc. "
    "0001013488", "BJRI", "BJs RESTAURANTS INC"
    "0001001290", "BAP", "CREDICORP LTD"
    "0000937966", "ASML", "ASML HOLDING NV"
    "0001527636", "ATHM", "Autohome Inc."
    "0000050104", "ANDV", "ANDEAVOR"
    "0001596532", "ANET", "Arista Networks, Inc."
    "0001521332", "APTV", "Aptiv PLC"
    
    #print (records)
    #insert data into the table
    cur.executemany ('INSERT INTO cik_ticker_name VALUES (?, ?, ?)', records)

    con.commit ()
    con.close ()
    
    
def lookup_cik_ticker(ticker):
    import requests
    import sys
    from bs4 import BeautifulSoup as BSoup
    
    req = requests.get(\
        "https://www.sec.gov/cgi-bin/browse-edgar?CIK={:s}&owner=exclude&action=getcompany&Find=Search"\
        .format(ticker.lower()))
    ## Check for errors encountered in trying to get that url.
    try:
        req.raise_for_status ()
    except:
        print(" -- {}:\n\t\t{}".format (sys.exc_info ()[0], req.url))
        return None
    soup = BSoup(req.content, "lxml")
    ## Search for the tag that contains the company name.
    conmTag = soup.find("span", {"class": "companyName"})
    if not conmTag:
        print("Unable to find the company name for ticker {:s}.".format(ticker))
        return None
    ## Search for the a-ref tag that links to "all company filings". Its text contains the CIK.
    atags = soup.findAll("a")
    atagCik = None
    for t in atags:
        if "see all company filings" in t.text:
            atagCik = t
    if not atagCik:
        print("Unable to find the a-ref tag with the CIK for ticker {:s}.".format(ticker))
        return None
    cik = atagCik.text.split(" ")[0]
    conm = conmTag.text.split("CIK")[0].strip()
    return (str(cik), ticker, str(conm))


def get_cik_for_ticker_db(ticker, conn):
    """Lookup the CIK for a ticker in an active connection to my edgar database."""
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM cik_ticker_name WHERE ticker=?;''',(ticker,))
    res = cursor.fetchall()
    ## If this ticker is not in the lookup database, try to search on the web.
    if not res:
        record = lookup_cik_ticker(ticker)
        if not record:
            print("Error! Unable to look up '{:s}' on www.sec.gov.".format(ticker))
            cik = None
        else:
            #insert data into the table
            cursor.execute ('INSERT INTO cik_ticker_name VALUES (?, ?, ?)', record)
            conn.commit ()
            cik = record[0]
    else:
        try: 
            cik = res[0][0]
        except BaseException as be:
            print("Unable to locate CIK for ticker {:s}.".format(ticker))
            print("Record in database: {:s}".format(str(res)))
            print(str(be))
            cik = None
    return cik