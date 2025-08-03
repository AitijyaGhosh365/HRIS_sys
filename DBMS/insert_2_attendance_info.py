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


def insert_or_update_attendance(company_id, employee_id, date, status, check_in=None, check_out=None):
    try:
        conn = psycopg2.connect(
            host=SUPABASE_HOST,
            port=SUPABASE_PORT,
            database=SUPABASE_DATABASE,
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD
        )
        cur = conn.cursor()

        # Define table names
        employee_table = f'"{company_id}_EMPLOYEES_INFO"'
        attendance_table = f'"{company_id}_ATTENDANCE"'

        # Step 1: Check if employee exists
        cur.execute(f"SELECT 1 FROM {employee_table} WHERE id = %s", (employee_id,))
        if cur.fetchone() is None:
            print("❌ Employee does not exist.")
            return 404  # Not found

        # Step 2: Insert or update attendance
        insert_query = f"""
        INSERT INTO {attendance_table} (employee_id, date, status, check_in, check_out)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (employee_id, date) DO UPDATE
        SET status = EXCLUDED.status,
            check_in = EXCLUDED.check_in,
            check_out = EXCLUDED.check_out;
        """

        cur.execute(insert_query, (employee_id, date, status, check_in, check_out))
        conn.commit()
        print("✅ Attendance recorded.")
        return 200

    except Exception as e:
        print("❌ Error:", e)
        return 500

    finally:
        if conn:
            cur.close()
            conn.close()


# Example Usage
if __name__ == "__main__":
    company_id = "18"
    employee_id = 10000000
    date = "2025-08-01"
    status = "present"
    check_in = "09:00"
    check_out = "17:00"

    result = insert_or_update_attendance(company_id, employee_id, date, status, check_in, check_out)
    print("Status Code:", result)
