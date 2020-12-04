"""Traverse the repositories."""
# pylint: disable = import-error
from pydriller import RepositoryMining
from github import Github
from github import RateLimitExceededException
import pandas as pd
import numpy as np
import os


import json
from datetime import datetime, timezone
import time
import urllib
import calendar

def wait(seconds):
    print("Waiting for {} seconds ...".format(seconds))
    time.sleep(seconds)
    print("Done waiting - resume!")

def api_wait(githb):
    rl = githb.get_rate_limit()
    current_time = calendar.timegm(time.gmtime())
    if  rl.core.remaining <= 10:  # extra margin of safety
        reset_time = calendar.timegm(rl.core.reset.timetuple())
        wait(reset_time - current_time + 10.0)
    elif rl.search.remaining <= 2:
        reset_time = calendar.timegm(rl.search.reset.timetuple())
        wait(reset_time - current_time + 10.0)