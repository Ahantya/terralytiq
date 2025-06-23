# testing
import pandas as pd
import CEDA

PCF = pd.read_csv("PCF.csv")
conversion = pd.read_csv("conversion.csv")


# first 25 rows are just text, so we need to remove them
PCF = PCF.iloc[26: ]
# first column is just empty
PCF = PCF.drop(PCF.columns[0], axis=1)
# product code and description aren't really needed
PCF = PCF.drop(index=[28])

print(PCF.head())

print(conversion.head())


