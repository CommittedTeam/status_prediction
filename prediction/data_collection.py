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

def search_repos(token,languages):
    githb = Github(token)
    repo_list = []
    for language in languages:
        repos = githb.search_repositories(query="language:{} size:>50000 stars:>10000".format(language),sort = 'updated', order = 'desc')
        for repo in repos:
            repos_stats = {
                "language": repo.language,
                "project_name": repo.full_name,
                "total_commits": repo.get_commits().totalCount,
                "html_url": repo.html_url
            }
            repo_list.append(repos_stats)
    return repo_list

def final_status(statuses,completion):
    fails = ["error","failure","cancelled","timed_out","action_required","startup_failure"]
    final_status = []
    if not statuses and not completion:
        final_status.append("N/A")
    for status in fails:
        if status in statuses:
            final_status.append("fail")
            break
    if "pending" in statuses:
        final_status.append("pending")
    else:
        final_status.append("pass")

    return final_status[0]
