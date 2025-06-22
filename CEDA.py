# testing
import pandas as pd

CEDA = pd.read_csv("CEDA.csv")


CEDA = CEDA.iloc[25: ]
CEDA = CEDA.drop(CEDA.columns[0], axis=1)
CEDA = CEDA.drop(26)

print(CEDA.head())
