import cot_reports as cot

df = cot.cot_year(year=2025, cot_report_type="disaggregated_fut")
print([m for m in df["Market_and_Exchange_Names"].unique() if "SUGAR" in m.upper()])
print([c for c in df.columns if "M_Money" in c or "MMoney" in c or "Money" in c])