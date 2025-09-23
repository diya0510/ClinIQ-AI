import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    conn_str=(
         f"DRIVER={{{os.getenv('DB_DRIVER')}}};"
         f"SERVER={os.getenv('DB_SERVER')};"
         f"DATABASE={os.getenv('DB_NAME')};"
         f"Trusted_Connection={os.getenv('DB_TRUSTED_CONNECTION')};"
    )
    return pyodbc.connect(conn_str)