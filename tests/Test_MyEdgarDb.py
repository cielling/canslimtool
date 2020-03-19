import unittest
from sys import path
path.insert(0, '..')
from MyEdgarDb import *
import sqlite3

class TestMyEdgarDb(unittest.TestCase):
	def setUp(self):
		"""Set up a mock database."""
		self.conn = sqlite3.connect(":memory:")
		cur = self.conn.cursor()
		
		#cmd = "'CREATE TABLE IF NOT EXISTS idx (cik TEXT, conm TEXT, type TEXT, date TEXT, path TEXT)'"
		#cur.execute(cmd)
		
		cmd = 'CREATE TABLE cik_ticker_name (cik TEXT, ticker TEXT, name TEXT)'
		cur.execute(cmd)
		
		cmd = 'INSERT INTO cik_ticker_name VALUES (?, ?, ?)'
		record = ("0001596532", "ANET", "Arista Networks, Inc.")
		cur.execute (cmd, record)
		
		self.conn.commit()
		
	def tearDown(self):
		self.conn.close()
		
	def test_get_cik_for_ticker_db_ANET_exists(self):
		ticker = "ANET"
		expect = "0001596532"
		result = get_cik_for_ticker_db(ticker, self.conn)
		self.assertEqual(expect, result)


if __name__ == '__main__':
    unittest.main()