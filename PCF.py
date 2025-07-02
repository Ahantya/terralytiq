# testing
import pandas as pd
import CEDA

PCF = pd.read_csv("PCF.csv")
conversion = pd.read_csv("conversion.csv")
conversion.columns = ['HS', 'NAICS']


# first 25 rows are just text, so we need to remove them
PCF = PCF.iloc[26: ]
# first column is just empty
PCF = PCF.drop(PCF.columns[0], axis=1)
# product code and description aren't really needed
PCF = PCF.drop(index=[28])

#print(PCF.head())

#print(conversion.head())

# convert them both to string and remove the .0 so we don't get value errors
conversion['HS'] = conversion['HS'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
hsCodes = PCF.iloc[1].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)

hs_df = hsCodes.reset_index() # creates an new index for each them in this dataframe 
hs_df.columns = ['colname', 'HS'] # gets a clean table of product hs codes for eahc column

merged = hs_df.merge(conversion, on='HS', how='left') # merges with conversion table, keep all the rows on the left even if there is no match on the right side with naics

# merged has naics and hs codes now 


ceda_long = CEDA.ceda_long

print(ceda_long)


pcf_data = PCF.iloc[26:].reset_index(drop=True)


pcf_data.columns = PCF.iloc[27]
pcf_data = pcf_data[2:]  


pcf_long = pd.melt(
    pcf_data,
    id_vars=[pcf_data.columns[0]],  
    var_name='product_code',
    value_name='carbon_intensity'
)


pcf_long = pcf_long.rename(columns={pcf_data.columns[0]: 'country'})




print(pcf_long)


# look at aluminum 331313 for naics and 







