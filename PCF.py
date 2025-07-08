import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import CEDA

# --- Load Data ---
PCF = pd.read_csv("PCF.csv")
conversion = pd.read_csv("conversion.csv")
conversion.columns = ['HS', 'NAICS']

# --- Clean PCF ---
PCF = PCF.iloc[26:]  # Skip first 26 rows of text
PCF = PCF.drop(PCF.columns[0], axis=1)  # Drop empty first column
PCF = PCF.drop(index=[28])

# --- Clean HS codes from header ---
hsCodes = PCF.iloc[1].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
hs_df = hsCodes.reset_index()
hs_df.columns = ['colname', 'HS']

# --- Merge with HS → NAICS conversion ---
conversion['HS'] = conversion['HS'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
merged = hs_df.merge(conversion, on='HS', how='left')  # Get NAICS by column name

# --- Reshape PCF to long format ---
pcf_data = PCF.iloc[0:].reset_index(drop=True)
pcf_data.columns = hsCodes.values
pcf_data = pcf_data[2:]  # Skip header rows again

# print(pcf_data)


pcf_long = pd.melt(
    pcf_data,
    id_vars=[pcf_data.columns[0]],
    var_name='product_code',
    value_name='carbon_intensity'
)
pcf_long = pcf_long.rename(columns={pcf_data.columns[0]: 'country'})


## --- Prepare PCF ---

conversion['HS'] = conversion['HS'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
pcf_long['product_code'] = pcf_long['product_code'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)

pcf_with_naics = pcf_long.merge(
    conversion[['HS', 'NAICS']],
    left_on='product_code',
    right_on='HS',
    how='left'
)

# Drop rows where we couldn’t find a NAICS
pcf_with_naics = pcf_with_naics.dropna(subset=['NAICS'])
pcf_with_naics['NAICS'] = pcf_with_naics['NAICS'].astype(str).str.strip()

# --- Prepare CEDA ---
ceda_long = CEDA.ceda_long.copy()

# Clean product_code to match HS format
ceda_long['NAICS'] = ceda_long['product_code'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)

# Rename to match for plotting
ceda_long = ceda_long.rename(columns={'carbonIntensity': 'emissions'})
pcf_with_naics = pcf_with_naics.rename(columns={'carbon_intensity': 'emissions'})

naics_alias = {
    '331312': '331313',  # Treat both as aluminum
}

country_alias = {
    'United States of America': 'United States',
    'Republic of Korea': 'South Korea',
    'Russian Federation': 'Russia',
    'Viet Nam': 'Vietnam',
    'China, mainland': 'China',
    # add more if needed
}

pcf_with_naics['NAICS'] = pcf_with_naics['NAICS'].replace(naics_alias)
ceda_long['NAICS'] = ceda_long['NAICS'].replace(naics_alias)

# fix aliases

pcf_with_naics['country'] = pcf_with_naics['country'].replace(country_alias)
ceda_long['country'] = ceda_long['country'].replace(country_alias)


# --- Filter for relevant NAICS and countries ---
naics_codes = ['331110', '331313', '331420', '325211']  # steel, aluminum, copper, polyethylene
countries = ['China', 'Brazil', 'India', 'Germany', 'Japan', 'United States']


ceda_filtered = ceda_long[ceda_long['NAICS'].isin(naics_codes) & ceda_long['country'].isin(countries)].copy()
pcf_filtered = pcf_with_naics[pcf_with_naics['NAICS'].isin(naics_codes) & pcf_with_naics['country'].isin(countries)].copy()

# Tag sources
ceda_filtered['Source'] = 'CEDA'
pcf_filtered['Source'] = 'PCF'

#print("Rows for Brazil:\n", pcf_data[pcf_data['Product HS Code'] == 'Brazil'])

# --- Combine for plotting ---
naics_names = {
    '331110': 'Steel',
    '331313': 'Aluminum',
    '331420': 'Copper',
    '325211': 'Polyethylene'
}

plot_df = pd.concat([
    ceda_filtered[['country', 'NAICS', 'emissions', 'Source']],
    pcf_filtered[['country', 'NAICS', 'emissions', 'Source']]
])
plot_df['NAICS_Label'] = plot_df['NAICS'].map(lambda x: f"{x} ({naics_names.get(x, 'Unknown')})")


usa_baseline = ceda_filtered[ceda_filtered['country'] == 'United States'][['NAICS', 'emissions']]
usa_baseline = usa_baseline.rename(columns={'emissions': 'usa_emissions'})
plot_df = plot_df.merge(usa_baseline, on='NAICS', how='left')
plot_df['emissions'] = pd.to_numeric(plot_df['emissions'], errors='coerce')
plot_df['usa_emissions'] = pd.to_numeric(plot_df['usa_emissions'], errors='coerce')
plot_df['Pct_Increase'] = ((plot_df['emissions'] - plot_df['usa_emissions']) / plot_df['usa_emissions']) * 100



sns.set(style='whitegrid')

# Define the order of countries if you want a consistent order
country_order = ['China', 'Brazil', 'India', 'Germany', 'Japan', 'United States']


# Split into two DataFrames
pcf_plot = plot_df[plot_df['Source'] == 'PCF'].copy()

print("Rows for Brazil:\n", pcf_plot[pcf_plot['country'] == 'Brazil'])
print(pcf_plot)
ceda_plot = plot_df[plot_df['Source'] == 'CEDA'].copy()

# Remove United States (always 0% increase)
pcf_plot = pcf_plot[pcf_plot['country'] != 'United States']
ceda_plot = ceda_plot[ceda_plot['country'] != 'United States']

# --- Plot PCF ---
g1 = sns.catplot(
    data=pcf_plot,
    x='country',
    y='Pct_Increase',
    col='NAICS_Label',
    kind='bar',
    ci=None,
    palette='Blues',
    col_wrap=3,
    height=4,
    aspect=1.2,
    order=[c for c in country_order if c != 'United States']
)
g1.set_axis_labels("Country", "% Increase in Emissions vs USA (Ahantya Sharma)")
g1.set_titles("PCF | {col_name}")

for ax in g1.axes.flatten():
    for label in ax.get_xticklabels():
        label.set_rotation(45)
        label.set_horizontalalignment('right')

plt.tight_layout()
plt.show()

# --- Plot CEDA ---
g2 = sns.catplot(
    data=ceda_plot,
    x='country',
    y='Pct_Increase',
    col='NAICS_Label',
    kind='bar',
    ci=None,
    palette='Greens',
    col_wrap=3,
    height=4,
    aspect=1.2,
    order=[c for c in country_order if c != 'United States']
)
g2.set_axis_labels("Country", "% Increase in Emissions vs USA (Ahantya Sharma)")
g2.set_titles("CEDA | {col_name}")

for ax in g2.axes.flatten():
    for label in ax.get_xticklabels():
        label.set_rotation(45)
        label.set_horizontalalignment('right')

plt.tight_layout()
plt.show()