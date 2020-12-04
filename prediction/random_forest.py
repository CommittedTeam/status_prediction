import pandas as pd
import matplotlib.pyplot as plt
col_list = ["tr_status","git_diff_src_churn","git_num_all_built_commits","git_diff_test_churn","gh_diff_files_added","gh_diff_files_deleted","gh_diff_files_modified"]

rails_data = pd.read_csv("../data/rails.csv",low_memory=False, usecols=col_list)

status = [0 if x in ["failed","errored"] else 1 for x in rails_data["tr_status"]]


rails_data["tr_status"] = status

failed = 0
passed = 0
for i in rails_data["tr_status"]:
    if (i == 0):
        failed += 1
    else:
        passed += 1

print("failed: ", failed)
print("passed: ", passed)

# resampling

from collections import Counter
from sklearn.datasets import make_classification
from imblearn.over_sampling import SMOTE 
import numpy as np
from sklearn.utils.class_weight import compute_class_weight

targetNames = ["0","1"]



# print("length of tr_status: ",len(np.array(rails_data["tr_status"])))

# class_weights = compute_class_weight(class_weight = 'balanced', classes = np.unique(np.array(rails_data["tr_status"])), y = np.array(rails_data["tr_status"]))
# print("class weights: ", class_weights)

# X, y = make_classification(weights=class_weights, flip_y=0, n_samples=1000)
# print('Original dataset shape %s' % Counter(y))

# sm = SMOTE(random_state=42)
# X_res, y_res = sm.fit_resample(X, y)
# print('Resampled dataset shape %s' % Counter(y_res))
# # Use numpy to convert to arrays
import numpy as np
# Labels are the values we want to predict
labels = np.array(rails_data["tr_status"])



# Remove the labels from the features
# axis 1 refers to the columns
features = rails_data.drop("tr_status", axis = 1)
# Saving feature names for later use
feature_list = list(features.columns)
# Convert to numpy array
features = np.array(features)

from sklearn.model_selection import train_test_split
# Split the data into training and testing sets
train_features, test_features, train_labels, test_labels = train_test_split(features, labels, test_size = 0.25, random_state = 42)


# Import the model we are using
from sklearn.ensemble import RandomForestClassifier
# Instantiate model with 1000 decision trees [1.45728039 0.76115651]
rf = RandomForestClassifier(class_weight="balanced")
# Train the model on training data
rf.fit(train_features, train_labels)

from sklearn.metrics import classification_report
# evaluate the classifier
   

from sklearn.model_selection import KFold, StratifiedKFold, cross_val_score 
metric_names = ['f1', 'roc_auc', 'average_precision', 'accuracy', 'precision', 'recall']
scores_df = pd.DataFrame(index=metric_names, columns=["Stratified-CV"]) # to store the scores

scv = StratifiedKFold(n_splits=3)

for metric in metric_names:
    score = cross_val_score(rf, test_features, test_labels, scoring=metric, cv=scv).mean()
    scores_df.loc[metric] = [score]
print(scores_df)

#Get numerical feature importances

importances = list(rf.feature_importances_)
# List of tuples with variable and importance
feature_importances = [(feature, round(importance, 2)) for feature, importance in zip(feature_list, importances)]
# Sort the feature importances by most important first
feature_importances = sorted(feature_importances, key = lambda x: x[1], reverse = True)
# Print out the feature and importances 
[print('Variable: {:20} Importance: {}'.format(*pair)) for pair in feature_importances]




