import pandas as pd
import sqlite3
from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).resolve().parent

# File paths
csv_path = BASE_DIR / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
db_path = BASE_DIR / "data" / "processed" / "churn.db"

# Load CSV
df = pd.read_csv(csv_path)

# Convert TotalCharges to numeric because it contains blank spaces
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

# Drop rows with missing TotalCharges
df = df.dropna(subset=["TotalCharges"])

# Connect to SQLite database
conn = sqlite3.connect(db_path)

# Save dataframe as SQL table
df.to_sql("customers", conn, if_exists="replace", index=False)

# Close database connection
conn.close()

print("CSV loaded successfully into SQLite database.")
print(f"Rows loaded: {df.shape[0]}")
print(f"Columns loaded: {df.shape[1]}")
print(f"Database created at: {db_path}")