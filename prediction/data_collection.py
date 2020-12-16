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
            }
            repo_list.append(repos_stats)
    return repo_list
    
def parse_for_type(name):
    """Parse through file name and returns its format."""
    if "." in name:
        file_type, name = os.path.splitext(name)
        file_type += ""
        return name
    return name

def get_file_formats(files):
    """Create a list of unique file formats."""
    formats = []
    for file in files:
        current_format = parse_for_type(file)
        if current_format not in formats:
            formats.append(current_format)
    # sort data to ensure consistency for test
    formats = sorted(formats)
    return formats

def final_status(statuses):
    fails = ["error","failure","cancelled","timed_out","action_required","startup_failure"]
    final_status = []
    if not statuses:
        final_status.append("NA")
    for status in fails:
        if status in statuses:
            final_status.append("fail")
            break
    if "pending" in statuses:
        final_status.append("pending")
    else:
        final_status.append("pass")

    return final_status[0]


def commit_info(token,repos):
    githb = Github(token)
    checks_info = []
    for reponame in repos:
        repo = githb.get_repo(reponame)
        commits = repo.get_commits()
        
        for commit in commits:
            try:
                statuses = []
                checks = []
                file_names = []
                is_merged = []
                
                
                # files stats
                for commit_file in commit.files:
                    file_names.append(commit_file.filename)

                # pull request stats
                for pull in commit.get_pulls():
                    is_merged.append(pull.merged)
                if not is_merged:
                    is_merged.append(False)

                # Commit Status
                status = commit.get_combined_status()
                if status.statuses:
                    statuses.append(status.state)

                # Check run
                check_runs = commit.get_check_suites()
                for check_run in check_runs:
                    check_conclusion = check_run.conclusion
                    if check_conclusion is not None:
                        checks.append(check_conclusion)
                    if check_run.status == "in_progress":
                        checks.append("pending")

                checks = {
                    "repo_name": repo.full_name,
                    "repo_language": repo.language,
                    "total_commits": repo.get_commits().totalCount,
                    "commit_sha": commit.sha,
                    "commit_msg": commit.commit.message,
                    "num_parent_commits": len(commit.parents),
                    "merged_from_pull": is_merged,
                    "lines_added": commit.stats.additions,
                    "lines_deleted": commit.stats.deletions,
                    "lines_total": commit.stats.total,
                    "file_names": file_names,
                    "files_total": len(file_names),
                    "unique_file_formats": get_file_formats(file_names),
                    "num_unique_file_formats": len(get_file_formats(file_names)),
                    "statuses":statuses,
                    "checks": checks,
                    "combined": final_status(statuses + checks),
                }
                checks_info.append(checks)
                
            except StopIteration:
                break

            except RateLimitExceededException:
                api_wait(githb)
                continue
            
    return checks_info



