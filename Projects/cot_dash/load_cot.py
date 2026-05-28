"""CFTC Commitments of Traders loader.

Pulls the disaggregated futures report year-by-year, filters to a single
market, computes the Managed Money Net position, and returns a weekly
[Date, Managed_Money_Net] dataframe.
"""
from datetime import date

import pandas as pd
import cot_reports as cot
from analytics import rolling_percentile


def load_cot(
    start_year: int = 2016,
    end_year: int | None = None,
    market: str = 'SUGAR NO. 11',
) -> pd.DataFrame:
    """Return weekly Managed Money Net positioning for `market`.

    `end_year` defaults to the current calendar year so the dashboard does
    not need a code change each January.
    """
    if end_year is None:
        end_year = date.today().year

    # Pull each year separately so one bad year doesn't kill the whole load.
    cot_list = []
    for year in range(start_year, end_year + 1):
        print(f"Fetching COT data for {year}...")
        try:
            yearly_df = cot.cot_year(year=year, cot_report_type='disaggregated_fut')
            cot_list.append(yearly_df)
        except Exception as e:
            print(f"Could not fetch {year}: {e}")

    raw_cot_df = pd.concat(cot_list, ignore_index=True)

    market_df = raw_cot_df[
        raw_cot_df['Market_and_Exchange_Names'].str.contains(market, case=False)
    ].copy()

    market_df['Date'] = pd.to_datetime(market_df['Report_Date_as_YYYY-MM-DD'])

    # Managed Money Net = hedge-fund longs minus hedge-fund shorts.
    market_df['Managed_Money_Net'] = (
        market_df['M_Money_Positions_Long_All']
        - market_df['M_Money_Positions_Short_All']
    )

    market_df = market_df.sort_values('Date').reset_index(drop=True)
    market_df["MM_pct"] = rolling_percentile(market_df["Managed_Money_Net"])

    return market_df[['Date', 'Managed_Money_Net', 'MM_pct']]
    

if __name__ == '__main__':
    print(load_cot().tail())
