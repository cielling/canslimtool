def set_test_db():
    from sys import path
    path.insert(0, "..")
    from MyEdgarDb import get_list_sec_filings, get_cik_ticker_lookup_db, lookup_cik_ticker
    get_list_sec_filings (7, 'test_idx.db')
    get_cik_ticker_lookup_db ('test_idx.db')

def download_test_data():
    import sqlite3
    from datetime import datetime
    import pandas as pd
    testDir = "..\\TestData\\"
    testTickers = {
                "AAPL": [datetime(2014, 8, 1), datetime(2018, 8, 1)],
                "ACLS": [datetime(2014, 8, 31), datetime(2018, 8, 31)],
                "ADSK": [datetime(2014, 4, 15), datetime(2018, 4, 15)],
                "ALEX": [datetime(2015, 12, 31), datetime(2019, 12, 31)],
                "MMM": [datetime(2015, 7, 1), datetime(2019, 7, 1)],
                "NRP": [datetime(2015, 12, 31), datetime(2019, 12, 31)],
                "NVDA": [datetime(2015, 12, 31), datetime(2019, 12, 31)]
               }
    conn3 = sqlite3.connect('test_idx.db')
    cursor = conn3.cursor()
    for ticker in testTickers:
        #cursor.execute('''SELECT * FROM idx WHERE Symbol=?;''', ("ABBV",))
        cursor.execute('''SELECT * FROM cik_ticker_name WHERE ticker=?;''',(ticker,))
        res = cursor.fetchall()
        print(res)
        cursor.execute('''SELECT * FROM idx WHERE cik=?;''', (res[0][0],))
        recs = cursor.fetchall()
        print(len(recs))
        names = list(map(lambda x: x[0], cursor.description))
        #print(names)
        df = pd.DataFrame(data=recs, columns=names)
        df['date'] = pd.to_datetime(df['date'])
        beginDate = testTickers[ticker][0]
        endDate = testTickers[ticker][1]
        df1 = df[(df.date >= beginDate) & (df.date <= endDate)]
        ## Sort by date in descending order (most recent is first)
        df1.sort_values(by=['date'], inplace=True, ascending=False)
        df1[df1.type == "10-Q"].to_csv(testDir+ticker.lower()+"_all_10qs.csv", index=None)
        df1[df1.type == "10-K"].to_csv(testDir+ticker.lower()+"_all_10ks.csv", index=None)
    
    conn3.close()
        

if __name__ == "__main__":
    #set_test_db()
    download_test_data()