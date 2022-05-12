from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from joblib import dump

import pandas as pd


final_dataset = pd.read_csv('dataset_final.csv', header=0)

X_train, X_test, y_train, y_test = train_test_split(final_dataset.drop('state', axis=1), final_dataset['state'])

logmodel = LogisticRegression(solver='lbfgs', max_iter=10000)
logmodel.fit(X_train, y_train)

dump(logmodel, 'modelo_alterno.joblib')
