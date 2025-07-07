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
PCF = PCF.drop(index=[28])  # Drop unwanted row

# --- Clean HS codes from header ---
hsCodes = PCF.iloc[1].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
hs_df = hsCodes.reset_index()
hs_df.columns = ['colname', 'HS']

# --- Merge with HS → NAICS conversion ---
conversion['HS'] = conversion['HS'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
merged = hs_df.merge(conversion, on='HS', how='left')  # Get NAICS by column name

# --- Reshape PCF to long format ---
pcf_data = PCF.iloc[26:].reset_index(drop=True)
pcf_data.columns = hsCodes.values
pcf_data = pcf_data[2:]  # Skip header rows again


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

pcf_with_naics['NAICS'] = pcf_with_naics['NAICS'].replace(naics_alias)
ceda_long['NAICS'] = ceda_long['NAICS'].replace(naics_alias)

# --- Filter for relevant NAICS and countries ---
naics_codes = ['331110', '331313', '331420', '325211']  # steel, aluminum, copper, polyethylene
countries = ['China', 'Brazil', 'India', 'Germany', 'Japan']


ceda_filtered = ceda_long[ceda_long['NAICS'].isin(naics_codes) & ceda_long['country'].isin(countries)].copy()
pcf_filtered = pcf_with_naics[pcf_with_naics['NAICS'].isin(naics_codes) & pcf_with_naics['country'].isin(countries)].copy()

# Tag sources
ceda_filtered['Source'] = 'CEDA'
pcf_filtered['Source'] = 'PCF'

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


print(ceda_filtered['NAICS'].unique())


sns.set(style='whitegrid')

# Define the order of countries if you want a consistent order
country_order = ['China', 'Brazil', 'India', 'Germany', 'Japan']
# Create a categorical plot (barplot) faceted by NAICS
g = sns.catplot(
    data=plot_df,
    x='country',
    y='emissions',
    hue='Source',
    col='NAICS_Label',
    kind='bar',
    ci=None,
    palette='Set2',
    col_wrap=3,
    height=4,
    aspect=1.2,
    order=country_order
)


g.set_axis_labels("Country", "Emissions (kg CO₂e or similar)")
g.set_titles("NAICS: {col_name}")
g._legend.set_title('Data Source')

for ax in g.axes.flatten():
    for label in ax.get_xticklabels():
        label.set_rotation(45)
        label.set_horizontalalignment('right')

plt.tight_layout()
plt.show()