import pandas as pd

file_xlsx = "fr_with_errors.xlsx"
file_csv = "fr_with_errors.csv"

df = pd.read_excel(file_xlsx)
df.to_csv(file_csv, index=False)