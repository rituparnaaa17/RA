import os
import sys

# Add the parent directory to sys.path so we can resolve backend imports (if run from root)
sys.path.append(os.getcwd())

from sqlalchemy import text
from backend.db import engine
from output_adapter import print_success, print_error

def check_connection():
    try:
        print("Attempting to connect to database...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Connection successful! Result:", result.scalar())
            print_success("Database connection verified.")
    except Exception as e:
        print("Connection failed!")
        print_error(str(e))

if __name__ == "__main__":
    check_connection()
