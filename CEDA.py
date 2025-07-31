import pandas as pd

# Step 1: Load CEDA with header at row 27 (0-indexed)
CEDA = pd.read_csv("CEDA.csv", header=27)

CEDA = CEDA.drop(CEDA.columns[0], axis=1)

# Step 2: Drop the third column which holds the units ('kgCO2e/US Dollar')
CEDA_clean = CEDA.drop(columns=CEDA.columns[2])

# Step 3: Melt to long format
ceda_long = pd.melt(
    CEDA_clean,
    id_vars=[CEDA_clean.columns[0], CEDA_clean.columns[1]],  # 'Country Code', 'Country'
    var_name='product_code',
    value_name='carbonIntensity'
)

# Step 4: Convert carbon intensity to numeric
ceda_long['carbonIntensity'] = pd.to_numeric(ceda_long['carbonIntensity'], errors='coerce')


ceda_long = ceda_long.rename(columns={
    CEDA_clean.columns[0]: 'country_code',
    CEDA_clean.columns[1]: 'country'
})



# #import pandas as pd
# import plotly.graph_objects as go
# import plotly.express as px
# import dash
# from dash import dcc, html, Input, Output
# import CEDA

# # Data Processing (same as original)
# PCF = pd.read_csv("PCF.csv")
# conversion = pd.read_csv("conversion.csv")
# conversion.columns = ['HS', 'NAICS']

# PCF = PCF.iloc[26:].drop(PCF.columns[0], axis=1).drop(index=[28])
# hsCodes = PCF.iloc[1].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
# hs_df = hsCodes.reset_index()
# hs_df.columns = ['colname', 'HS']

# conversion['HS'] = conversion['HS'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
# merged = hs_df.merge(conversion, on='HS', how='left')

# pcf_data = PCF.iloc[0:].reset_index(drop=True)
# pcf_data.columns = hsCodes.values
# pcf_data = pcf_data[2:]

# pcf_long = pd.melt(pcf_data, id_vars=[pcf_data.columns[0]], var_name='product_code', value_name='carbon_intensity')
# pcf_long = pcf_long.rename(columns={pcf_data.columns[0]: 'country'})

# pcf_long['product_code'] = pcf_long['product_code'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
# pcf_with_naics = pcf_long.merge(conversion[['HS', 'NAICS']], left_on='product_code', right_on='HS', how='left')
# pcf_with_naics = pcf_with_naics.dropna(subset=['NAICS'])
# pcf_with_naics['NAICS'] = pcf_with_naics['NAICS'].astype(str).str.strip()

# ceda_long = CEDA.ceda_long.copy()
# ceda_long['NAICS'] = ceda_long['product_code'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
# ceda_long = ceda_long.rename(columns={'carbonIntensity': 'emissions'})
# pcf_with_naics = pcf_with_naics.rename(columns={'carbon_intensity': 'emissions'})

# # Apply aliases and filters
# naics_alias = {'331312': '331313'}
# country_alias = {
#     'United States of America': 'United States',
#     'United States Of America': 'United States',
#     'USA - Alabama': 'United States',
#     'USA - Alaska': 'United States',
#     'Republic of Korea': 'South Korea',
#     'Russian Federation': 'Russia',
#     'Viet Nam': 'Vietnam',
#     'China, mainland': 'China',
# }

# pcf_with_naics['NAICS'] = pcf_with_naics['NAICS'].replace(naics_alias)
# ceda_long['NAICS'] = ceda_long['NAICS'].replace(naics_alias)
# pcf_with_naics['country'] = pcf_with_naics['country'].replace(country_alias)
# ceda_long['country'] = ceda_long['country'].replace(country_alias)

# naics_codes = ['331110', '331313', '331420', '325211']
# countries = ['China', 'Brazil', 'India', 'Germany', 'Japan', 'United States']

# ceda_filtered = ceda_long[ceda_long['NAICS'].isin(naics_codes) & ceda_long['country'].isin(countries)].copy()
# pcf_filtered = pcf_with_naics[pcf_with_naics['NAICS'].isin(naics_codes) & pcf_with_naics['country'].isin(countries)].copy()

# ceda_filtered['Source'] = 'CEDA'
# pcf_filtered['Source'] = 'PCF'

# naics_names = {'331110': 'Steel', '331313': 'Aluminum', '331420': 'Copper', '325211': 'Polyethylene'}

# # Combine data
# plot_df = pd.concat([
#     ceda_filtered[['country', 'NAICS', 'emissions', 'Source']],
#     pcf_filtered[['country', 'NAICS', 'emissions', 'Source']]
# ], sort=False)

# plot_df['NAICS_Label'] = plot_df['NAICS'].map(lambda x: f"{x} ({naics_names.get(x, 'Unknown')})")

# # Calculate USA baseline
# usa_baseline = plot_df[plot_df['country'] == 'United States'][['NAICS', 'Source', 'emissions']]
# usa_baseline = usa_baseline.rename(columns={'emissions': 'usa_emissions'})
# plot_df = plot_df.merge(usa_baseline, on=['NAICS', 'Source'], how='left')
# plot_df['emissions'] = pd.to_numeric(plot_df['emissions'], errors='coerce')
# plot_df['usa_emissions'] = pd.to_numeric(plot_df['usa_emissions'], errors='coerce')
# plot_df['Pct_Increase'] = ((plot_df['emissions'] - plot_df['usa_emissions']) / plot_df['usa_emissions']) * 100

# # Initialize Dash app
# app = dash.Dash(__name__)

# # Define app layout
# app.layout = html.Div([
#     html.H1("Carbon Emissions Dashboard", 
#             style={'text-align': 'center', 'margin-bottom': '30px', 'color': '#2c3e50'}),
    
#     # Control panel
#     html.Div([
#         html.Div([
#             html.Label("Select Data Source:", style={'font-weight': 'bold', 'margin-bottom': '10px'}),
#             dcc.RadioItems(
#                 id='data-source',
#                 options=[
#                     {'label': 'CEDA', 'value': 'CEDA'},
#                     {'label': 'PCF', 'value': 'PCF'}
#                 ],
#                 value='CEDA',
#                 style={'margin-bottom': '20px'}
#             )
#         ], style={'width': '48%', 'display': 'inline-block', 'vertical-align': 'top'}),
        
#         html.Div([
#             html.Label("Select Element:", style={'font-weight': 'bold', 'margin-bottom': '10px'}),
#             dcc.Dropdown(
#                 id='element-dropdown',
#                 options=[
#                     {'label': 'Steel (331110)', 'value': '331110'},
#                     {'label': 'Aluminum (331313)', 'value': '331313'},
#                     {'label': 'Copper (331420)', 'value': '331420'},
#                     {'label': 'Polyethylene (325211)', 'value': '325211'}
#                 ],
#                 value='331110',
#                 style={'margin-bottom': '20px'}
#             )
#         ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
#     ], style={'margin-bottom': '30px', 'padding': '20px', 'background-color': '#f8f9fa', 'border-radius': '10px'}),
    
#     # Chart container
#     html.Div([
#         dcc.Graph(id='emissions-chart')
#     ], style={'margin-bottom': '30px'}),
    
#     # Summary statistics
#     html.Div(id='summary-stats', style={'padding': '20px', 'background-color': '#f8f9fa', 'border-radius': '10px'})
# ])

# # Callback for updating the chart
# @app.callback(
#     [Output('emissions-chart', 'figure'),
#      Output('summary-stats', 'children')],
#     [Input('data-source', 'value'),
#      Input('element-dropdown', 'value')]
# )
# def update_chart(data_source, selected_naics):
#     # Filter data based on selections
#     filtered_df = plot_df[
#         (plot_df['Source'] == data_source) & 
#         (plot_df['NAICS'] == selected_naics) &
#         (plot_df['country'] != 'United States')  # Exclude USA since it's the baseline
#     ].copy()
    
#     # Remove duplicates
#     filtered_df = filtered_df.drop_duplicates(subset=['country', 'NAICS'], keep='first')
    
#     # Sort by percentage increase for better visualization
#     filtered_df = filtered_df.sort_values('Pct_Increase', ascending=True)
    
#     # Create the bar chart
#     fig = px.bar(
#         filtered_df,
#         x='country',
#         y='Pct_Increase',
#         title=f'{data_source} | {naics_names.get(selected_naics, "Unknown")} ({selected_naics}) - % Increase vs USA',
#         labels={'Pct_Increase': '% Increase in Emissions vs USA', 'country': 'Country'},
#         color='Pct_Increase',
#         color_continuous_scale='RdYlBu_r'
#     )
    
#     # Update layout
#     fig.update_layout(
#         title_font_size=16,
#         xaxis_title_font_size=14,
#         yaxis_title_font_size=14,
#         height=500,
#         showlegend=False
#     )
    
#     # Add a horizontal line at 0% for reference
#     fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
    
#     # Rotate x-axis labels if needed
#     fig.update_xaxes(tickangle=45)
    
#     # Create summary statistics
#     if not filtered_df.empty:
#         max_increase = filtered_df['Pct_Increase'].max()
#         min_increase = filtered_df['Pct_Increase'].min()
#         avg_increase = filtered_df['Pct_Increase'].mean()
        
#         max_country = filtered_df.loc[filtered_df['Pct_Increase'].idxmax(), 'country']
#         min_country = filtered_df.loc[filtered_df['Pct_Increase'].idxmin(), 'country']
        
#         summary = html.Div([
#             html.H3(f"Summary Statistics - {naics_names.get(selected_naics, 'Unknown')} ({data_source})", 
#                    style={'margin-bottom': '15px', 'color': '#2c3e50'}),
#             html.Div([
#                 html.Div([
#                     html.H4(f"{max_increase:.1f}%", style={'color': '#e74c3c', 'margin': '0'}),
#                     html.P(f"Highest increase ({max_country})", style={'margin': '0', 'font-size': '14px'})
#                 ], style={'width': '30%', 'display': 'inline-block', 'text-align': 'center'}),
                
#                 html.Div([
#                     html.H4(f"{avg_increase:.1f}%", style={'color': '#3498db', 'margin': '0'}),
#                     html.P("Average increase", style={'margin': '0', 'font-size': '14px'})
#                 ], style={'width': '30%', 'display': 'inline-block', 'text-align': 'center'}),
                
#                 html.Div([
#                     html.H4(f"{min_increase:.1f}%", style={'color': '#27ae60', 'margin': '0'}),
#                     html.P(f"Lowest increase ({min_country})", style={'margin': '0', 'font-size': '14px'})
#                 ], style={'width': '30%', 'display': 'inline-block', 'text-align': 'center'})
#             ])
#         ])
#     else:
#         summary = html.Div([
#             html.H3("No data available for this selection", style={'color': '#e74c3c'})
#         ])
    
#     return fig, summary

# # Run the app
# if __name__ == '__main__':
#     app.run(debug=True)   