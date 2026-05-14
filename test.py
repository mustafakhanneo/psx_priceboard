import psxdata

q = psxdata.quote("KEL")

print("=== TYPE ===")
print(type(q))

print("\n=== ALL COLUMNS ===")
print(q.columns.tolist())

print("\n=== FULL ROW (no truncation) ===")
import pandas as pd
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", None)
print(q)

print("\n=== VALUES AS DICT ===")
print(q.iloc[0].to_dict())