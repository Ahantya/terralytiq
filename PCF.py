import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import CEDA
from matplotlib.ticker import FixedLocator

# Load and prepare PCF data
PCF = pd.read_csv("PCF.csv")
conversion = pd.read_csv("conversion.csv")
conversion.columns = ['HS', 'NAICS']

PCF = PCF.iloc[26:].drop(PCF.columns[0], axis=1).drop(index=[28])
hsCodes = PCF.iloc[1].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)

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

# Melt to long format
pcf_long = pd.melt(
    pcf_data,
    id_vars=[pcf_data.columns[0]],
    var_name='product_code',
    value_name='carbon_intensity'
)
pcf_long = pcf_long.rename(columns={pcf_data.columns[0]: 'country'})

# Merge NAICS and Material
pcf_long['product_code'] = pcf_long['product_code'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
pcf_with_naics = pcf_long.merge(merged[['HS', 'NAICS', 'Material']], left_on='product_code', right_on='HS', how='left')
pcf_with_naics = pcf_with_naics.dropna(subset=['NAICS'])
pcf_with_naics['NAICS'] = pcf_with_naics['NAICS'].astype(str).str.strip()

# Prepare CEDA data
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

def fix_plot(g, data):
    for ax in g.axes.flatten():
        # Get the countries used in this subplot
        title = ax.get_title().split(' | ')[-1]
        countries = data[data['NAICS_Label'] == title]['country'].dropna().unique()
        countries = [c for c in country_order if c in countries]  # keep order consistent
        ax.set_xticks(range(len(countries)))
        ax.set_xticklabels(countries, rotation=45, ha='right')

def fix_plotMaterial(g):
    for ax in g.axes.flatten():
        # Set proper x-tick labels
        countries = ax.get_xticks()
        labels = [t.get_text() for t in ax.get_xticklabels()]
        ax.set_xticks(countries)
        ax.set_xticklabels(labels, rotation=45, ha='right')


# ✅ Fix for PCF plot
g1 = sns.catplot(
    data=pcf_plot,
    x='country',              
    y='Pct_Increase',
    col='NAICS_Label',
    kind='bar',
    errorbar=None,
    palette='Blues',         
    col_wrap=3,
    height=4,
    aspect=1.2,
    order=[c for c in country_order if c != 'United States']
)
g1.set_axis_labels("Country", "% Increase in Emissions vs USA (Ahantya Sharma)")
g1.set_titles("PCF | {col_name}")
fix_plot(g1, pcf_plot)
plt.tight_layout()
plt.show()


g2 = sns.catplot(
    data=ceda_plot,
    x='country',
    y='Pct_Increase',
    col='NAICS_Label',
    kind='bar',
    errorbar=None,
    palette='Greens',
    col_wrap=3,
    height=4,
    aspect=1.2,
    order=[c for c in country_order if c != 'United States']
)
g2.set_axis_labels("Country", "% Increase in Emissions vs USA (Ahantya Sharma)")
g2.set_titles("CEDA | {col_name}")
fix_plot(g2, ceda_plot)
plt.tight_layout()
plt.show()


# --- General steel product code 720610 plot ---
# Filter only for steel and product_code = 720610
steel_720610_pcf = pcf_with_naics[
    (pcf_with_naics['product_code'] == '720610') &
    (pcf_with_naics['Material'].str.lower() == 'steel')
].copy()

# Clean emissions column
steel_720610_pcf['emissions'] = pd.to_numeric(steel_720610_pcf['emissions'], errors='coerce')
steel_720610_pcf = steel_720610_pcf.dropna(subset=['emissions'])

# Keep only the first entry per country
first_emissions_per_country = steel_720610_pcf.groupby('country', as_index=False).first()

# REMEMBER THIS

# Get USA baseline
usa_baseline_value = first_emissions_per_country[
    first_emissions_per_country['country'] == 'United States'
]['emissions'].values[0]

print(f"USA baseline emission for Steel (720610): {usa_baseline_value}")

# Add % Increase vs USA
first_emissions_per_country['Pct_Increase'] = (
    (first_emissions_per_country['emissions'] - usa_baseline_value) / usa_baseline_value
) * 100

# Optional: filter to countries in your desired display order
plot_data = first_emissions_per_country[first_emissions_per_country['country'].isin(country_order)]

print(plot_data)

# Plot
g = sns.catplot(
    data=plot_data,
    x='country',
    y='Pct_Increase',
    kind='bar',
    errorbar=None,
    hue='country',
    palette='Blues',
    legend=False,
    height=5,
    aspect=1.5,
    order=country_order
)

g.set_axis_labels("Country", "% Increase in Emissions vs USA")
g.set_titles("Steel (Product Code 720610) | PCF vs USA")
fix_plotMaterial(g)
plt.tight_layout()
plt.show()


code = '760421'
aluminum_760421_pcf = pcf_with_naics[
    (pcf_with_naics['product_code'] == code)
].copy()

# Clean emissions
aluminum_760421_pcf['emissions'] = pd.to_numeric(aluminum_760421_pcf['emissions'], errors='coerce')
aluminum_760421_pcf = aluminum_760421_pcf.dropna(subset=['emissions'])

# Keep only the first entry per country
first_emissions_per_country = aluminum_760421_pcf.groupby('country', as_index=False).first()

# Get USA baseline
usa_baseline_value = first_emissions_per_country[
    first_emissions_per_country['country'] == 'United States'
]['emissions'].values[0]

print(f"USA baseline emission for Aluminum (760421): {usa_baseline_value}")

# Add % Increase vs USA
first_emissions_per_country['Pct_Increase'] = (
    (first_emissions_per_country['emissions'] - usa_baseline_value) / usa_baseline_value
) * 100

# Filter by country_order
plot_data = first_emissions_per_country[first_emissions_per_country['country'].isin(country_order)]

# Plot
g = sns.catplot(
    data=plot_data,
    x='country',
    y='Pct_Increase',
    kind='bar',
    errorbar=None,
    hue='country',
    palette='Oranges',
    legend=False,
    height=5,
    aspect=1.5,
    order=country_order
)

g.set_axis_labels("Country", "% Increase in Emissions vs USA")
g.set_titles("Aluminum (HS 760421) | PCF vs USA")
fix_plotMaterial(g)
plt.tight_layout()
plt.show()

# --- Copper product code 740811 plot ---

code = '740811'
copper_740811_pcf = pcf_with_naics[
    (pcf_with_naics['product_code'] == code)
].copy()

# Clean emissions
copper_740811_pcf['emissions'] = pd.to_numeric(copper_740811_pcf['emissions'], errors='coerce')
copper_740811_pcf = copper_740811_pcf.dropna(subset=['emissions'])

# Keep only the first entry per country
first_emissions_per_country = copper_740811_pcf.groupby('country', as_index=False).first()

# Get USA baseline
usa_baseline_value = first_emissions_per_country[
    first_emissions_per_country['country'] == 'United States'
]['emissions'].values[0]

print(f"USA baseline emission for Copper (740811): {usa_baseline_value}")

# Add % Increase vs USA
first_emissions_per_country['Pct_Increase'] = (
    (first_emissions_per_country['emissions'] - usa_baseline_value) / usa_baseline_value
) * 100

# Filter by country order
plot_data = first_emissions_per_country[first_emissions_per_country['country'].isin(country_order)]

# Plot
g = sns.catplot(
    data=plot_data,
    x='country',
    y='Pct_Increase',
    kind='bar',
    errorbar=None,
    hue='country',
    palette='Reds',
    legend=False,
    height=5,
    aspect=1.5,
    order=country_order
)

g.set_axis_labels("Country", "% Increase in Emissions vs USA")
g.set_titles("Copper (HS 740811) | PCF vs USA")
fix_plotMaterial(g)
plt.tight_layout()
plt.show()


# --- Polyethylene product code 390110 plot ---

code = '390110'
poly_390110_pcf = pcf_with_naics[
    (pcf_with_naics['product_code'] == code)
].copy()

# Clean emissions
poly_390110_pcf['emissions'] = pd.to_numeric(poly_390110_pcf['emissions'], errors='coerce')
poly_390110_pcf = poly_390110_pcf.dropna(subset=['emissions'])

# Keep only the first entry per country
first_emissions_per_country = poly_390110_pcf.groupby('country', as_index=False).first()

# Get USA baseline
usa_baseline_value = first_emissions_per_country[
    first_emissions_per_country['country'] == 'United States'
]['emissions'].values[0]

print(f"USA baseline emission for Polyethylene (390110): {usa_baseline_value}")

# Add % Increase vs USA
first_emissions_per_country['Pct_Increase'] = (
    (first_emissions_per_country['emissions'] - usa_baseline_value) / usa_baseline_value
) * 100

# Filter by country order
plot_data = first_emissions_per_country[first_emissions_per_country['country'].isin(country_order)]

# Plot
g = sns.catplot(
    data=plot_data,
    x='country',
    y='Pct_Increase',
    kind='bar',
    errorbar=None,
    hue='country',
    palette='Purples',
    legend=False,
    height=5,
    aspect=1.5,
    order=country_order
)

g.set_axis_labels("Country", "% Increase in Emissions vs USA")
g.set_titles("Polyethylene (HS 390110) | PCF vs USA")
fix_plotMaterial(g)
plt.tight_layout()
plt.show()


# spot check china brazil that should be lower than germany for ceda steel
# fix pcf numbers baseline

#1 positive trends are similar in ceda and pcf
#2 spread of percentages in ceda are bigger.
#3 china may be underestimated