import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import CEDA
from matplotlib.ticker import FixedLocator
import os

# Save directory
outdir = os.getcwd()  # current working directory

# Load PCF and conversion
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

# Long PCF format
pcf_long = pd.melt(
    pcf_data,
    id_vars=[pcf_data.columns[0]],
    var_name='product_code',
    value_name='carbon_intensity'
)
pcf_long = pcf_long.rename(columns={pcf_data.columns[0]: 'country'})
pcf_long['product_code'] = pcf_long['product_code'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)

pcf_with_naics = pcf_long.merge(merged[['HS', 'NAICS', 'Material']], left_on='product_code', right_on='HS', how='left')
pcf_with_naics = pcf_with_naics.dropna(subset=['NAICS'])
pcf_with_naics['NAICS'] = pcf_with_naics['NAICS'].astype(str).str.strip()

# CEDA
ceda_long = CEDA.ceda_long.copy()
ceda_long['NAICS'] = ceda_long['product_code'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
ceda_long = ceda_long.rename(columns={'carbonIntensity': 'emissions'})
pcf_with_naics = pcf_with_naics.rename(columns={'carbon_intensity': 'emissions'})

# Standardize country & NAICS
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
    # ... other mappings ...
}
pcf_with_naics['NAICS'] = pcf_with_naics['NAICS'].replace(naics_alias)
ceda_long['NAICS'] = ceda_long['NAICS'].replace(naics_alias)
pcf_with_naics['country'] = pcf_with_naics['country'].replace(country_alias)
ceda_long['country'] = ceda_long['country'].replace(country_alias)

sns.set_theme(style='whitegrid')

def fix_plotMaterial(g):
    for ax in g.axes.flatten():
        countries = ax.get_xticks()
        labels = [t.get_text() for t in ax.get_xticklabels()]
        ax.set_xticks(countries)
        ax.set_xticklabels(labels, rotation=45, ha='right')

# Load country list
with open('countries.txt', 'r') as f:
    country_order = [line.strip() for line in f if line.strip()]

# Material mapping
product_codes = {
    '720610': 'Steel',
    '760421': 'Aluminum',
    '740811': 'Copper',
    '390110': 'Polyethylene',
    '850760': 'Battery Cell',
    '540710': 'Textile',
    '853400': "Circuit",
    '390761': "Polyethylene (Plastics)"
}

naics_map = {
    '720610': '331110',    # Steel 
    '760421': '331313',    # Aluminum
    '740811': '331420',    # Copper 
    '390110': '325211',     # Polyethylene
    '850760': '335912',     # Battery Cell
    '540710': "313300",     # Textile
    '853400': "334418",     # Circuit Assembly
    '390761': "326160"     # Plastics
}

palette_map = {
    'Steel': 'Blues',
    'Aluminum': 'Oranges',
    'Copper': 'Reds',
    'Polyethylene': 'Purples',
    'Battery Cell': 'Greens'
}

# ---- BAR PLOTS ----
for code, material in product_codes.items():
    material_df = pcf_with_naics[pcf_with_naics['product_code'] == code].copy()
    material_df['emissions'] = pd.to_numeric(material_df['emissions'], errors='coerce')
    material_df = material_df.dropna(subset=['emissions'])
    
    # PCF
    pcf_summary = material_df.groupby('country', as_index=False).first()
    try:
        usa_value = pcf_summary[pcf_summary['country'] == 'United States']['emissions'].values[0]
    except IndexError:
        continue
    pcf_summary['Pct_Increase'] = ((pcf_summary['emissions'] - usa_value) / usa_value) * 100
    pcf_summary = pcf_summary[pcf_summary['country'].isin(country_order)]
    pcf_summary_no_us = pcf_summary[pcf_summary['country'] != 'United States']
    country_order_no_us = [c for c in country_order if c != 'United States']

    g1 = sns.catplot(
        data=pcf_summary_no_us,
        x='country',
        y='Pct_Increase',
        kind='bar',
        hue='country',
        palette=palette_map.get(material, 'gray'),
        legend=False,
        height=5,
        aspect=1.5,
        order=country_order_no_us
    )
    g1.set_axis_labels("Country", "% Increase in Emissions vs USA")
    g1.fig.suptitle(f"{material} (HS {code}) | PCF vs USA", fontsize=16)
    fix_plotMaterial(g1)
    plt.tight_layout()
    g1.savefig(os.path.join(outdir, f"{material}_{code}_PCF.png"))
    plt.close()

    # CEDA
    naics_code = naics_map.get(code)
    ceda_material = ceda_long[ceda_long['NAICS'] == naics_code].copy()
    try:
        usa_ceda_value = ceda_material[ceda_material['country'] == 'United States']['emissions'].values[0]
    except IndexError:
        continue
    ceda_summary = ceda_material.groupby('country', as_index=False).first()
    ceda_summary['Pct_Increase'] = ((ceda_summary['emissions'] - usa_ceda_value) / usa_ceda_value) * 100
    ceda_summary = ceda_summary[ceda_summary['country'].isin(country_order)]
    ceda_summary_no_us = ceda_summary[ceda_summary['country'] != 'United States']

    g2 = sns.catplot(
        data=ceda_summary_no_us,
        x='country',
        y='Pct_Increase',
        kind='bar',
        hue='country',
        palette=palette_map.get(material, 'gray'),
        legend=False,
        height=5,
        aspect=1.5,
        order=country_order_no_us
    )
    g2.set_axis_labels("Country", "% Increase in Emissions vs USA")
    g2.fig.suptitle(f"{material} (NAICS {code}) | CEDA vs USA", fontsize=16)
    fix_plotMaterial(g2)
    plt.tight_layout()
    g2.savefig(os.path.join(outdir, f"{material}_{code}_CEDA.png"))
    plt.close()

# ---- LINE PLOTS ----
for code, material in product_codes.items():
    naics_code = naics_map.get(code)
    if not naics_code:
        continue
    
    # PCF
    pcf_mat = pcf_with_naics[pcf_with_naics['product_code'] == code].copy()
    pcf_mat['emissions'] = pd.to_numeric(pcf_mat['emissions'], errors='coerce')
    pcf_mat = pcf_mat.dropna(subset=['emissions'])
    pcf_summary = pcf_mat.groupby('country', as_index=False).mean(numeric_only=True)
    try:
        usa_value_pcf = pcf_summary[pcf_summary['country'] == 'United States']['emissions'].values[0]
    except IndexError:
        continue
    pcf_summary['Pct_Increase'] = ((pcf_summary['emissions'] - usa_value_pcf) / usa_value_pcf) * 100
    pcf_summary['Source'] = 'PCF'

    # CEDA
    ceda_mat = ceda_long[ceda_long['NAICS'] == naics_code].copy()
    ceda_summary = ceda_mat.groupby('country', as_index=False).mean(numeric_only=True)
    try:
        usa_value_ceda = ceda_summary[ceda_summary['country'] == 'United States']['emissions'].values[0]
    except IndexError:
        continue
    ceda_summary['Pct_Increase'] = ((ceda_summary['emissions'] - usa_value_ceda) / usa_value_ceda) * 100
    ceda_summary['Source'] = 'CEDA'

    # Combine
    combined = pd.concat([
        pcf_summary[['country', 'Pct_Increase', 'Source']],
        ceda_summary[['country', 'Pct_Increase', 'Source']]
    ], ignore_index=True)
    combined = combined[combined['country'].isin(country_order)]
    combined = combined[combined['country'] != 'United States']

    plt.figure(figsize=(12, 6))
    sns.lineplot(
        data=combined,
        x='country',
        y='Pct_Increase',
        hue='Source',
        marker='o'
    )
    plt.xticks(rotation=45, ha='right')
    plt.xlabel("Country")
    plt.ylabel("% Increase in Emissions vs USA")
    plt.title(f"{material} | PCF vs CEDA (% Increase vs USA)")
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, f"{material}_{code}_Line.png"))
    plt.close()
