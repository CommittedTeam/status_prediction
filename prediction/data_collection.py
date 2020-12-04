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

def features(repos):
    """Create a list of dictionaries that contains commit info."""

    commit_list = []
    for repo in repos:
        commits = RepositoryMining(repo).traverse_commits()

        for commit in commits:

            line_added = 0
            line_removed = 0
            line_of_code = 0
            token_count = 0
            methods = []
            filename = []
            change_type = []

            for item in commit.modifications:
                # modifications is a list of files and its changes
                line_added += item.added
                line_removed += item.removed
                if item.nloc is not None:
                    line_of_code += item.nloc
                if item.token_count is not None:
                    token_count += item.token_count
                for method in item.changed_methods:
                    methods.append(method.name)
                filename.append(item.filename)
                change_type.append(item.change_type.name)

            single_commit_dict = {
                "project_name":commit.project_name,
                "hash": commit.hash,
                "commit_msg": commit.msg,
                "merge": commit.merge,
                "line_added": line_added,
                "line_removed": line_removed,
                "churns": (line_added - line_removed),
                "lines_of_code": line_of_code,
                "dmm_unit_size": commit.dmm_unit_size,
                "dmm_unit_complexity": commit.dmm_unit_complexity,
                "dmm_unit_interfacing": commit.dmm_unit_interfacing,
                "token_count": token_count,
                "num_modified_methods": len(methods),
                "num_modified_files": len(filename),
                "file_names": filename,
                "num_file_formats": len(get_file_formats(filename)),
                "file_formats": get_file_formats(filename),
                "num_change_type": len(get_file_formats(change_type)),
                "change_types": get_file_formats(change_type),
                
            }

            commit_list.append(single_commit_dict)

    return commit_list
