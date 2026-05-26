import pandas as pd

# Load the first two contracts as an example
DATA_PATH = '../../data/pull.xlsx'

# 1. Create an empty list to hold the price data
df_list = []

# 2. Loop through numbers 1 to 6
for i in range(1, 7):
    filename = f'SB{i}'
    column_name = f'SB{i}_Price'

    # Read the current sheet
    temp_df = pd.read_excel(DATA_PATH, sheet_name=filename, header=None, names=['Date', column_name])

    # Clean up rows with no prices
    temp_df = temp_df.dropna(subset=[column_name])
    
    # Set Date as the index so that pd.concat aligns them by Date
    # and we avoid getting 6 duplicate Date columns!
    temp_df = temp_df.set_index('Date')
    
    # 3. Add the cleaned dataframe to our list
    df_list.append(temp_df)

# 4. Combine all DataFrames in the list by their Date index
df = pd.concat(df_list, axis=1)

# Reset index to bring Date back as a single, clean column
df = df.reset_index()

# Sort by Date chronologically
df = df.sort_values(by='Date').reset_index(drop=True)

# Print tail to verify
print(df.tail())

    


