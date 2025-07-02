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

