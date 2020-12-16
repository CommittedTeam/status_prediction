import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from sklearn.datasets import make_classification
from imblearn.over_sampling import SMOTE 
import numpy as np
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import confusion_matrix
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_score, cross_validate
from sklearn.model_selection import train_test_split

data = pd.read_csv("../data/traindata.csv",index_col=0)
# encode the labels
status = [0 if x == "fail" else 1 for x in data["combined"]]

# Labels are the values we want to predict
labels = np.array(status)

# Remove the labels from the features
# axis 1 refers to the columns
features = data.drop("combined", axis = 1)
# Saving feature names for later use
feature_list = list(features.columns)
# Convert to numpy array
features = np.array(features)

# construct the training and testing splits
(trainData, testData, trainLabel, testLabel) = train_test_split(
    features, labels, test_size=0.3, random_state=0, stratify=labels
)
# the model we are using, set class_weight to balanced because the classes are imbalanced

model = RandomForestClassifier(random_state=0,class_weight="balanced")


metric_names = ['f1', 'roc_auc', 'average_precision', 'accuracy', 'precision', 'recall']
scores_df = pd.DataFrame(index=metric_names, columns=["Stratified-CV"]) # to store the scores

scv = StratifiedKFold(n_splits=10)

for metric in metric_names:
    score = cross_val_score(model, trainData, trainLabel, scoring=metric, cv=scv).mean()
    scores_df.loc[metric] = [score]
print(scores_df)



