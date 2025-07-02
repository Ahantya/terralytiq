# testing
import pandas as pd

CEDA = pd.read_csv("CEDA.csv", header=27)


CEDA = CEDA.iloc[26: ]
CEDAClean = CEDA.drop(CEDA.columns[0], axis=1)
#CEDA = CEDA.drop(26)

print(CEDAClean.head())
