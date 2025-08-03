from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import psycopg2
from functools import lru_cache
from fastapi.responses import JSONResponse
from fastapi import Query

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


@lru_cache(maxsize=1)
def get_all_employees_cached():
    print("⏳ Fetching from database (cache miss)...")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, first_name, job_title, email FROM "18_EMPLOYEES_INFO" ORDER BY id')
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

@app.get("/autocomplete")
def autocomplete(prefix: str = Query(..., min_length=4)):
    try:
        employees = get_all_employees_cached()
        # Unique first names starting with prefix (case-insensitive)
        matches = list({e[1] for e in employees if e[1].lower().startswith(prefix.lower())})
        return JSONResponse(matches[:10])  # return top 10 matches
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, field: str = None, value: str = None):
    try:
        employees = get_all_employees_cached()

        if field and value:
            allowed_fields = ['id', 'first_name', 'email']
            if field not in allowed_fields:
                return HTMLResponse(content="Invalid filter field", status_code=400)

            if field == 'id':
                filtered = [e for e in employees if str(e[0]) == value]
            elif field == 'first_name':
                filtered = [e for e in employees if value.lower() in e[1].lower()]
            elif field == 'email':
                filtered = [e for e in employees if value.lower() in e[3].lower()]
        else:
            filtered = employees

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "employees": [(e[0], e[1], e[2]) for e in filtered]  # drop email before sending to template
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
