import pandas as pd
import numpy as np
import math
import seaborn as sns
import matplotlib.pyplot as plt
import seaborn as sns


def plot_frequencies(data,path="../plots/statuses.png"):
    sns.set(style="whitegrid")

    keys, counts = np.unique(data, return_counts=True)

    sns.barplot(x = keys, y = counts)
    plt.savefig(path)


def select_commits(data,coloumn='combined',item_list=["pass", "fail"]):
    passed_failed = data[data[coloumn].isin(item_list)]
    return passed_failed

features = ["lines_total","lines_added","lines_deleted","files_total","num_unique_file_formats","num_parent_commits","merged_from_pull","combined"]
data = pd.read_csv("../data/raw_data.csv",usecols=features)

# visualize the combined status frequencies
plot_frequencies(data['combined'])

# select commits with pass or fail status
select_commits(data).to_csv("../data/traindata.csv",header=True)


