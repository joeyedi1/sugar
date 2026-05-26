"""Sugar No. 11 futures price loader.

Reads SB1..SBn price series from an Excel workbook (one sheet per contract),
merges them on Date, and returns a tidy daily dataframe with a calendar-spread
column already computed.
"""
import pandas as pd

DATA_PATH = '../../data/pull.xlsx'


def load_prices(data_path: str = DATA_PATH, n_contracts: int = 6) -> pd.DataFrame:
    """Return a daily price dataframe with columns:
        Date, SB1_Price ... SBn_Price, SB1_SB2_Spread.
    """
    df_list = []
    for i in range(1, n_contracts + 1):
        col = f'SB{i}_Price'
        temp_df = pd.read_excel(data_path, sheet_name=f'SB{i}', header=None, names=['Date', col])
        temp_df = temp_df.dropna(subset=[col])

        # Set Date as the index so pd.concat aligns the n series on Date
        # instead of producing n duplicate Date columns side-by-side.
        temp_df = temp_df.set_index('Date')
        df_list.append(temp_df)

    df = pd.concat(df_list, axis=1)
    df = df.reset_index()
    df = df.sort_values(by='Date').reset_index(drop=True)

    df['SB1_SB2_Spread'] = df['SB1_Price'] - df['SB2_Price']
    return df


if __name__ == '__main__':
    print(load_prices().tail())
