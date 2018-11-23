import requests
from bs4 import BeautifulSoup as BSoup
import pandas as pd
import csv
import requests
import os
from datetime import datetime, timedelta
from SecFiling import SecFiling
import traceback

class SecFiling20F(SecFiling):
    def getCurrentValue(self, tagList):
        """Finds the tag for the current date from a list of tags, and returns its value."""
        return super(SecFiling20F, self).getCurrentValue(tagList, 365, 5)

