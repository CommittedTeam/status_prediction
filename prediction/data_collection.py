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


def status_info(token,repos):
    githb = Github(token)
    checks_info = []
    for reponame in repos:
        repo = githb.get_repo(reponame)
        commits = repo.get_commits()
        workflows = repo.get_workflow_runs(event="push")

        for commit in commits.reversed:
            try:
                statuses = []
                workflows_stats = []
                checks = []
                completion = []

                status = commit.get_combined_status()
                if status.statuses:
                    statuses.append(status.state)

                for workflow in workflows.reversed:
                    if workflow.head_sha == commit.sha:

                        conclusion = workflow.conclusion
                        if conclusion is not None:
                            workflows_stats.append(conclusion)

                
                check_suites = commit.get_check_runs()
                for check_suite in check_suites.reversed:
                    check_conclusion = check_suite.conclusion
                    if not workflows_stats and check_conclusion is not None:
                        checks.append(check_conclusion)
                    if check_conclusion is not None and check_suite.app.name != "GitHub Actions":
                        checks.append(check_conclusion)

                    check_suite_completion = check_suite.status
                    if check_suite_completion == "completed":
                        completion.append(check_suite_completion)
                    elif check_suite_completion == "in_progress":
                        completion.append(check_suite_completion)
                        checks.append("pending")

                checks = {

                    "commit_sha": commit.sha,
                    "completion_status": completion,
                    "statuses":statuses,
                    "workflows": workflows_stats,
                    "checks": checks,
                    "combined": final_status((statuses + checks + workflows_stats),completion)
                }
                
                checks_info.append(checks)

            except StopIteration:
                break

            except RateLimitExceededException:
                api_wait(githb)
                continue
            
    return checks_info
