from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import psycopg2

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# PostgreSQL connection
def get_db_connection():
    return psycopg2.connect(
        dbname="postgres",
        user="postgres.gbpfzccmztlsqxwynslk",
        password="Happy_Birthday123",
        host="aws-0-ap-south-1.pooler.supabase.com",
        port="6543"
    )

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, field: str = None, value: str = None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if field and value:
            allowed_fields = ['id', 'first_name', 'email']
            if field not in allowed_fields:
                return HTMLResponse(content="Invalid filter field", status_code=400)

            if field == 'id':
                query = f'SELECT id, first_name, job_title FROM "18_EMPLOYEES_INFO" WHERE {field} = %s ORDER BY id'
                cur.execute(query, (int(value),))
            else:
                query = f'SELECT id, first_name, job_title FROM "18_EMPLOYEES_INFO" WHERE {field} ILIKE %s ORDER BY id'
                cur.execute(query, (f"%{value}%",))
        else:
            cur.execute('SELECT id, first_name, job_title FROM "18_EMPLOYEES_INFO" ORDER BY id')

        employees = cur.fetchall()

        cur.close()
        conn.close()

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "employees": employees
        })

    except Exception as e:
        return HTMLResponse(content=f"Error: {e}", status_code=500)



@app.get("/employee/{emp_id}", response_class=HTMLResponse)
def view_employee(emp_id: int, request: Request):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get basic employee info
        cur.execute('SELECT * FROM "18_EMPLOYEES_INFO" WHERE id = %s', (emp_id,))
        columns = [desc[0] for desc in cur.description]
        employee_data = cur.fetchone()
        employee = dict(zip(columns, employee_data))

        # Get attendance
        cur.execute('SELECT * FROM "18_ATTENDANCE" WHERE id = %s', (emp_id,))
        attendance = cur.fetchall()

        # Get leaves
        cur.execute('SELECT * FROM "18_LEAVE_TYPE" WHERE id = %s', (emp_id,))
        leaves = cur.fetchall()

        cur.close()
        conn.close()

        return templates.TemplateResponse("employee.html", {
            "request": request,
            "employee": employee,
            "attendance": attendance,
            "leaves": leaves
        })

    except Exception as e:
        return HTMLResponse(content=f"Error: {e}", status_code=500)
