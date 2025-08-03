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


def create_attendance_table(company_id):
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

        employee_table = f'"{company_id}_EMPLOYEES_INFO"'
        attendance_table = f'"{company_id}_ATTENDANCE"'

        create_query = f"""
        CREATE TABLE IF NOT EXISTS {attendance_table} (
            employee_id BIGINT REFERENCES {employee_table}(id) ON DELETE CASCADE,
            date DATE NOT NULL,
            status VARCHAR(20) CHECK (status IN ('present', 'absent', 'leave')),
            check_in TIME,
            check_out TIME,
            PRIMARY KEY (employee_id, date)
        );
        """

        cur.execute(create_query)
        conn.commit()
        cur.close()
        conn.close()
        return 200  # Success

    except Exception as e:
        print("SQL Error:", e)
        return 500  # SQL error


if __name__ == "__main__":
    company_id = "18"
    status = create_attendance_table(company_id)
    if status == 200:
        print("✅ Attendance table created successfully.")
    else:
        print("❌ Failed to create attendance table.")
