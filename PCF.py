import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import CEDA

PCF = pd.read_csv("PCF.csv")
conversion = pd.read_csv("conversion.csv")
conversion.columns = ['HS', 'NAICS']


PCF = PCF.iloc[26:].drop(PCF.columns[0], axis=1).drop(index=[28])
hsCodes = PCF.iloc[1].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)

# Material names from first row (e.g. "aluminum", "acetone", etc.)
material_names = PCF.iloc[0].astype(str).str.strip().reset_index(drop=True)
hs_df = pd.DataFrame({
    'colname': PCF.columns,
    'HS': hsCodes.values,
    'Material': material_names.values
})

 
conversion['HS'] = conversion['HS'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
merged = hs_df.merge(conversion, on='HS', how='left')


pcf_data = PCF.reset_index(drop=True)
pcf_data.columns = hsCodes.values
pcf_data = pcf_data[2:]
pcf_data.columns = pcf_data.columns.astype(str)  

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


print(pcf_with_naics[pcf_with_naics['NAICS'] == '331313']['Material'].unique())


general_steel_pcf = pcf_with_naics[
    (pcf_with_naics['NAICS'] == '331110') &
    (pcf_with_naics['Material'].str.lower() == 'steel') &
    (pcf_with_naics['country'] != 'United States')
].copy()

# Get USA general steel baseline
usa_general_steel = pcf_with_naics[
    (pcf_with_naics['NAICS'] == '331110') &
    (pcf_with_naics['Material'].str.lower() == 'steel') &
    (pcf_with_naics['country'] == 'United States')
][['product_code', 'emissions']].rename(columns={'emissions': 'usa_emissions'})

# Merge USA baseline into comparison data
general_steel_pcf = general_steel_pcf.merge(usa_general_steel, on='product_code', how='left')

# Calculate percent increase vs. USA
general_steel_pcf['emissions'] = pd.to_numeric(general_steel_pcf['emissions'], errors='coerce')
general_steel_pcf['usa_emissions'] = pd.to_numeric(general_steel_pcf['usa_emissions'], errors='coerce')
general_steel_pcf['Pct_Increase'] = ((general_steel_pcf['emissions'] - general_steel_pcf['usa_emissions']) / general_steel_pcf['usa_emissions']) * 100
general_steel_pcf = general_steel_pcf.dropna(subset=['Pct_Increase'])

country_order = ['China', 'Brazil', 'India', 'Germany', 'Japan']

# Filter only those countries
general_steel_pcf = general_steel_pcf[general_steel_pcf['country'].isin(country_order)]

# Set theme
sns.set_theme(style='whitegrid')

# Facet by country
g = sns.catplot(
    data=general_steel_pcf,
    x='product_code',
    y='Pct_Increase',
    col='country',
    kind='bar',
    errorbar=None,
    palette='Blues',
    col_order=country_order,
    height=4,
    aspect=1.1
)

g.set_axis_labels("Product Code", "% Increase in Emissions vs USA")
g.set_titles("{col_name}")
for ax in g.axes.flatten():
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.show()


######


# Filter for product code 760421 (aluminum extrusion)
code = '760421'
aluminum_760421_pcf = pcf_with_naics[
    (pcf_with_naics['product_code'] == code) &
    (pcf_with_naics['country'] != 'United States')
].copy()

# Get the USA baseline for product code 760421
usa_760421 = pcf_with_naics[
    (pcf_with_naics['product_code'] == code) &
    (pcf_with_naics['country'] == 'United States')
][['product_code', 'emissions']].rename(columns={'emissions': 'usa_emissions'})

# Merge to compute % increase vs USA
aluminum_760421_pcf = aluminum_760421_pcf.merge(usa_760421, on='product_code', how='left')

aluminum_760421_pcf['emissions'] = pd.to_numeric(aluminum_760421_pcf['emissions'], errors='coerce')
aluminum_760421_pcf['usa_emissions'] = pd.to_numeric(aluminum_760421_pcf['usa_emissions'], errors='coerce')
aluminum_760421_pcf['Pct_Increase'] = (
    (aluminum_760421_pcf['emissions'] - aluminum_760421_pcf['usa_emissions']) /
    aluminum_760421_pcf['usa_emissions']
) * 100

# Keep only the selected countries
country_order = ['China', 'Brazil', 'India', 'Germany', 'Japan']
aluminum_760421_pcf = aluminum_760421_pcf[aluminum_760421_pcf['country'].isin(country_order)]

# Plot
sns.set_theme(style='whitegrid')
g = sns.catplot(
    data=aluminum_760421_pcf,
    x='country',
    y='Pct_Increase',
    kind='bar',
    errorbar=None,  
    palette='Oranges',
    height=5,
    aspect=1.5,
    order=country_order
)

g.set_axis_labels("Country", "% Increase in Emissions vs USA")
g.set_titles("Aluminum (HS 760421) | PCF vs USA")
for ax in g.axes.flatten():
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.show()


#### 

code = '740811'
copper_740811_pcf = pcf_with_naics[
    (pcf_with_naics['product_code'] == code) &
    (pcf_with_naics['country'] != 'United States')
].copy()

# Get USA baseline for 740811
usa_740811 = pcf_with_naics[
    (pcf_with_naics['product_code'] == code) &
    (pcf_with_naics['country'] == 'United States')
][['product_code', 'emissions']].rename(columns={'emissions': 'usa_emissions'})

# Merge for % increase
copper_740811_pcf = copper_740811_pcf.merge(usa_740811, on='product_code', how='left')

copper_740811_pcf['emissions'] = pd.to_numeric(copper_740811_pcf['emissions'], errors='coerce')
copper_740811_pcf['usa_emissions'] = pd.to_numeric(copper_740811_pcf['usa_emissions'], errors='coerce')
copper_740811_pcf['Pct_Increase'] = (
    (copper_740811_pcf['emissions'] - copper_740811_pcf['usa_emissions']) /
    copper_740811_pcf['usa_emissions']
) * 100

# Limit to relevant countries
country_order = ['China', 'Brazil', 'India', 'Germany', 'Japan']
copper_740811_pcf = copper_740811_pcf[copper_740811_pcf['country'].isin(country_order)]

# Plot
sns.set_theme(style='whitegrid')
g = sns.catplot(
    data=copper_740811_pcf,
    x='country',
    y='Pct_Increase',
    kind='bar',
    errorbar=None,
    palette='Reds',
    height=5,
    aspect=1.5,
    order=country_order
)

g.set_axis_labels("Country", "% Increase in Emissions vs USA")
g.set_titles("Copper (HS 740811) | PCF vs USA")
for ax in g.axes.flatten():
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.show()


#### 

# Filter for product code 390110 (polyethylene)
code = '390110'
poly_390110_pcf = pcf_with_naics[
    (pcf_with_naics['product_code'] == code) &
    (pcf_with_naics['country'] != 'United States')
].copy()

# Get USA baseline for 390110
usa_390110 = pcf_with_naics[
    (pcf_with_naics['product_code'] == code) &
    (pcf_with_naics['country'] == 'United States')
][['product_code', 'emissions']].rename(columns={'emissions': 'usa_emissions'})

# Merge and calculate % increase
poly_390110_pcf = poly_390110_pcf.merge(usa_390110, on='product_code', how='left')

poly_390110_pcf['emissions'] = pd.to_numeric(poly_390110_pcf['emissions'], errors='coerce')
poly_390110_pcf['usa_emissions'] = pd.to_numeric(poly_390110_pcf['usa_emissions'], errors='coerce')
poly_390110_pcf['Pct_Increase'] = (
    (poly_390110_pcf['emissions'] - poly_390110_pcf['usa_emissions']) /
    poly_390110_pcf['usa_emissions']
) * 100

# Limit to relevant countries
country_order = ['China', 'Brazil', 'India', 'Germany', 'Japan']
poly_390110_pcf = poly_390110_pcf[poly_390110_pcf['country'].isin(country_order)]

# Plot
sns.set_theme(style='whitegrid')
g = sns.catplot(
    data=poly_390110_pcf,
    x='country',
    y='Pct_Increase',
    kind='bar',
    errorbar=None,
    palette='Purples',
    height=5,
    aspect=1.5,
    order=country_order
)

g.set_axis_labels("Country", "% Increase in Emissions vs USA")
g.set_titles("Polyethylene (HS 390110) | PCF vs USA")
for ax in g.axes.flatten():
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.show()


steel_pct_increase = plot_df[
    (plot_df['NAICS'] == '331110') &
    (plot_df['country'].isin(['China', 'Brazil', 'India', 'Germany', 'Japan']))
]
steel_pct_agg = steel_pct_increase.groupby(['country', 'Source'], as_index=False)['Pct_Increase'].mean()


steel_pct_pivot = steel_pct_agg.pivot(index='country', columns='Source', values='Pct_Increase')

print("Percent Increase in Emissions vs USA for NAICS 331110 (Steel):")
print(steel_pct_pivot.round(2))


# spot check china brazil that should be lower than germany for ceda steel
# fix pcf numbers baseline

#1 positive trends are similar in ceda and pcf
#2 spread of percentages in ceda are bigger.
#3 china may be underestimated