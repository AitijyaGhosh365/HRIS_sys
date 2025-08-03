import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
SUPABASE_HOST = os.getenv("SUPABASE_HOST")
SUPABASE_PORT = os.getenv("SUPABASE_PORT")
SUPABASE_DATABASE = os.getenv("SUPABASE_DATABASE")
SUPABASE_USER = os.getenv("SUPABASE_USER")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD")


def insert_company_2_COMPANY_INFO(company_name):
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

        # Ensure UUID extension and table
        cur.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
        cur.execute("""
            CREATE TABLE IF NOT EXISTS "COMPANY_INFO" (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                company_name VARCHAR
            );
        """)
        conn.commit()

        # Insert company name
        cur.execute("""
            INSERT INTO "COMPANY_INFO" (company_name) VALUES (%s);
        """, (company_name,))
        conn.commit()

        # Cleanup
        cur.close()
        conn.close()

        return 200  # Success

    except Exception:
        return 500  # SQL execution failure


# ✅ Example usage
if __name__ == "__main__":
    insert_company_2_COMPANY_INFO("AJ's Company")
