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


def insert_employee(company_id, employee_data):
    """
    Insert a single employee into {company_id}_EMPLOYEES_INFO.
    
    Returns: (status_code, inserted_id or None)
    """
    try:
        conn = psycopg2.connect(
            host=SUPABASE_HOST,
            port=SUPABASE_PORT,
            database=SUPABASE_DATABASE,
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD
        )
    except Exception:
        return 500, None  # Connection error

    try:
        cur = conn.cursor()

        table_name = f'"{company_id}_EMPLOYEES_INFO"'

        insert_query = f"""
            INSERT INTO {table_name} (
                first_name, middle_name, last_name, email, phone_number,
                dept_id, hire_date, job_title, salary, status, role, dob
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id;
        """

        values = (
            employee_data.get("first_name"),
            employee_data.get("middle_name"),
            employee_data.get("last_name"),
            employee_data.get("email"),
            employee_data.get("phone_number"),
            employee_data.get("dept_id"),
            employee_data.get("hire_date"),
            employee_data.get("job_title"),
            employee_data.get("salary"),
            employee_data.get("status"),
            employee_data.get("role"),
            employee_data.get("dob"),
        )

        # Execute and return ID
        cur.execute(insert_query, values)
        inserted_id = cur.fetchone()[0]
        conn.commit()

        cur.close()
        conn.close()

        return 200, inserted_id

    except Exception:
        return 500, None  # SQL or insertion error


# ✅ Example usage
if __name__ == "__main__":
    company_id = "18"

    employee_data = {
        "first_name": "Alice",
        "middle_name": "B",
        "last_name": "Smith",
        "email": "alice.smith@example.com",
        "phone_number": "9876543210",
        "dept_id": "HR01",
        "hire_date": "2024-01-10",
        "job_title": "HR Manager",
        "salary": 82000.00,
        "status": "Active",
        "role": "HR",
        "dob": "1990-11-22"
    }

    status, new_id = insert_employee(company_id, employee_data)
    if status == 200:
        print(f"✅ Employee inserted with ID: {new_id}")
    else:
        print("❌ Failed to insert employee.")
