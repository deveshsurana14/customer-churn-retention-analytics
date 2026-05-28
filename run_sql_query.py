import sqlite3
import pandas as pd
from pathlib import Path
import sys

# Base project directory
BASE_DIR = Path(__file__).resolve().parent

# Database path
db_path = BASE_DIR / "data" / "processed" / "churn.db"

# Default query file
default_query = "01_overall_churn_rate.sql"

# Get query filename from terminal argument
query_file = sys.argv[1] if len(sys.argv) > 1 else default_query

# SQL query path
query_path = BASE_DIR / "sql" / query_file

# Check if query file exists
if not query_path.exists():
    print(f"SQL file not found: {query_path}")
    sys.exit(1)

# Connect to database
conn = sqlite3.connect(db_path)

# Read query
with open(query_path, "r") as file:
    query = file.read()

# Run query
result = pd.read_sql_query(query, conn)

# Display output
print(f"\nRunning query: {query_file}\n")
print(result)

# Close connection
conn.close()