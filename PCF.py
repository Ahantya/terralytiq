import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import CEDA

# Load data
PCF = pd.read_csv("PCF.csv")
conversion = pd.read_csv("conversion.csv")
conversion.columns = ['HS', 'NAICS']

# Prepare PCF
PCF = PCF.iloc[26:].drop(PCF.columns[0], axis=1).drop(index=[28])
hsCodes = PCF.iloc[1].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)

# Material names from first row (e.g. "aluminum", "acetone", etc.)
material_names = PCF.iloc[0].astype(str).str.strip().reset_index(drop=True)
hs_df = pd.DataFrame({
    'colname': PCF.columns,
    'HS': hsCodes.values,
    'Material': material_names.values
})

# Merge with conversion
conversion['HS'] = conversion['HS'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
merged = hs_df.merge(conversion, on='HS', how='left')

# Set correct headers and drop top metadata rows
pcf_data = PCF.reset_index(drop=True)
pcf_data.columns = hsCodes.values
pcf_data = pcf_data[2:]
pcf_data.columns = pcf_data.columns.astype(str)  # Ensure string column names

# Melt into long format
pcf_long = pd.melt(
    pcf_data,
    id_vars=[pcf_data.columns[0]],
    var_name='product_code',
    value_name='carbon_intensity'
)
pcf_long = pcf_long.rename(columns={pcf_data.columns[0]: 'country'})

# Add NAICS and material name
pcf_long['product_code'] = pcf_long['product_code'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
pcf_with_naics = pcf_long.merge(merged[['HS', 'NAICS', 'Material']], left_on='product_code', right_on='HS', how='left')
pcf_with_naics = pcf_with_naics.dropna(subset=['NAICS'])
pcf_with_naics['NAICS'] = pcf_with_naics['NAICS'].astype(str).str.strip()

# Prepare CEDA
ceda_long = CEDA.ceda_long.copy()
ceda_long['NAICS'] = ceda_long['product_code'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
ceda_long = ceda_long.rename(columns={'carbonIntensity': 'emissions'})
pcf_with_naics = pcf_with_naics.rename(columns={'carbon_intensity': 'emissions'})

# Harmonize codes and country names
naics_alias = {'331312': '331313'}
country_alias = {
    'United States of America': 'United States',
    'United States Of America': 'United States',
    'USA - Alabama': 'United States',
    'USA - Alaska': 'United States',
    'Republic of Korea': 'South Korea',
    'Russian Federation': 'Russia',
    'Viet Nam': 'Vietnam',
    'China, mainland': 'China',
}

pcf_with_naics['NAICS'] = pcf_with_naics['NAICS'].replace(naics_alias)
ceda_long['NAICS'] = ceda_long['NAICS'].replace(naics_alias)
pcf_with_naics['country'] = pcf_with_naics['country'].replace(country_alias)
ceda_long['country'] = ceda_long['country'].replace(country_alias)

# Focused NAICS and countries
naics_codes = ['331110', '331313', '331420', '325211']
countries = ['China', 'Brazil', 'India', 'Germany', 'Japan', 'United States']

ceda_filtered = ceda_long[ceda_long['NAICS'].isin(naics_codes) & ceda_long['country'].isin(countries)].copy()
pcf_filtered = pcf_with_naics[pcf_with_naics['NAICS'].isin(naics_codes) & pcf_with_naics['country'].isin(countries)].copy()

ceda_filtered['Source'] = 'CEDA'
pcf_filtered['Source'] = 'PCF'

naics_names = {
    '331110': 'Steel',
    '331313': 'Aluminum',
    '331420': 'Copper',
    '325211': 'Polyethylene'
}

plot_df = pd.concat([
    ceda_filtered[['country', 'NAICS', 'emissions', 'Source']],
    pcf_filtered[['country', 'NAICS', 'emissions', 'Source']]
], sort=False)

plot_df['NAICS_Label'] = plot_df['NAICS'].map(lambda x: f"{x} ({naics_names.get(x, 'Unknown')})")

usa_baseline = plot_df[plot_df['country'] == 'United States'][['NAICS', 'Source', 'emissions']]
usa_baseline = usa_baseline.rename(columns={'emissions': 'usa_emissions'})
plot_df = plot_df.merge(usa_baseline, on=['NAICS', 'Source'], how='left')
plot_df['emissions'] = pd.to_numeric(plot_df['emissions'], errors='coerce')
plot_df['usa_emissions'] = pd.to_numeric(plot_df['usa_emissions'], errors='coerce')
plot_df['Pct_Increase'] = ((plot_df['emissions'] - plot_df['usa_emissions']) / plot_df['usa_emissions']) * 100

sns.set_theme(style='whitegrid')
country_order = ['China', 'Brazil', 'India', 'Germany', 'Japan', 'United States']

pcf_plot = plot_df[plot_df['Source'] == 'PCF'].copy()
ceda_plot = plot_df[plot_df['Source'] == 'CEDA'].copy()

pcf_plot = pcf_plot[pcf_plot['country'] != 'United States']
ceda_plot = ceda_plot[ceda_plot['country'] != 'United States']

pcf_plot = pcf_plot.drop_duplicates(subset=['country', 'NAICS'], keep='first')

g1 = sns.catplot(
    data=pcf_plot, x='country', y='Pct_Increase', col='NAICS_Label', kind='bar', ci=None, palette='Blues',
    col_wrap=3, height=4, aspect=1.2, order=[c for c in country_order if c != 'United States']
)
g1.set_axis_labels("Country", "% Increase in Emissions vs USA (Ahantya Sharma)")
g1.set_titles("PCF | {col_name}")
for ax in g1.axes.flatten():
    for label in ax.get_xticklabels():
        label.set_rotation(45)
        label.set_horizontalalignment('right')
plt.tight_layout()
plt.show()

g2 = sns.catplot(
    data=ceda_plot, x='country', y='Pct_Increase', col='NAICS_Label', kind='bar', ci=None, palette='Greens',
    col_wrap=3, height=4, aspect=1.2, order=[c for c in country_order if c != 'United States']
)
g2.set_axis_labels("Country", "% Increase in Emissions vs USA (Ahantya Sharma)")
g2.set_titles("CEDA | {col_name}")
for ax in g2.axes.flatten():
    for label in ax.get_xticklabels():
        label.set_rotation(45)
        label.set_horizontalalignment('right')
plt.tight_layout()
plt.show()

# ✅ Print check: include material name
germany_steel_pcf = pcf_with_naics[
    (pcf_with_naics['country'] == 'Germany') &
    (pcf_with_naics['NAICS'] == '331110')
]

print("Original PCF emissions for Germany (Steel - NAICS 331110):")
print(germany_steel_pcf[['country', 'product_code', 'Material', 'emissions', 'NAICS']])


# material name from pcf column and add the ceda value from the naics code

# options of steel materials for PCF as there are different product codes matching to the same CEDA


#Steel - Steel (machined)
# Polyethylene - Polyetheylene (ethane cracking)
# Copper  - Copper (wire)
# Aluminum  - Aluminum Casting (machined)


# structured way to expand this idea 