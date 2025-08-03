import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get credentials
SUPABASE_HOST = os.getenv("SUPABASE_HOST")
SUPABASE_PORT = os.getenv("SUPABASE_PORT")
SUPABASE_DATABASE = os.getenv("SUPABASE_DATABASE")
SUPABASE_USER = os.getenv("SUPABASE_USER")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD")


def create_employees_table(company_id):
    try:
        conn = psycopg2.connect(
            host=SUPABASE_HOST,
            port=SUPABASE_PORT,
            database=SUPABASE_DATABASE,
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD
        )
    except Exception:
        return 500  # Connection error

    try:
        cur = conn.cursor()

        # Enable UUID generator
        cur.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

        # Construct table name safely (quotes to preserve case and underscores)
        table_name = f'"{company_id}_EMPLOYEES_INFO"'

        # Create table query
        create_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY (START WITH 10000000 INCREMENT BY 1),
            first_name VARCHAR NOT NULL,
            middle_name VARCHAR,
            last_name VARCHAR NOT NULL,
            email VARCHAR NOT NULL UNIQUE,
            phone_number VARCHAR,
            dept_id VARCHAR NOT NULL,
            hire_date DATE NOT NULL,
            job_title VARCHAR NOT NULL,
            salary NUMERIC(10, 2),
            status VARCHAR,
            role VARCHAR,
            dob DATE
        );
        """

        cur.execute(create_query)
        conn.commit()
        cur.close()
        conn.close()
        return 200  # Success

    except Exception:
        return 500  # SQL error


# ✅ Example usage
if __name__ == "__main__":
    company_id = "18"  # You can change this
    status = create_employees_table(company_id)
    if status == 200:
        print("✅ Table created successfully.")
    else:
        print("❌ Failed to create table.")
