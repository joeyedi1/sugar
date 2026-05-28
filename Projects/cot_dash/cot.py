from load_cot import load_cot
from analytics import rolling_percentile

# Pull the most recent MM net from COT
# cot_data = load_cot()

# latest = cot_data.sort_values("Date").iloc[-1]

# print(f"{latest['Date']:%Y-%m-%d}: {latest['Managed_Money_Net']:,.0f}")

# Rolling Percentile
cot_data = load_cot().sort_values("Date").reset_index(drop=True)
cot_data["MM_pct"] = rolling_percentile(cot_data["Managed_Money_Net"])
print(cot_data["MM_pct"].first_valid_index())
print(cot_data["MM_pct"].min())
print(cot_data["MM_pct"].max())
# print(cot_data[["Date", "Managed_Money_Net", "MM_pct"]].tail())

# # Rate of Change
# cot_sorted = cot_data.sort_values("Date")
# cot_sorted["MM_Change"] = cot_sorted["Managed_Money_Net"].diff()
# print(cot_sorted[["Date", "Managed_Money_Net", "MM_Change"]].tail(5))