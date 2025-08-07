from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import psycopg2
from functools import lru_cache
from fastapi.responses import JSONResponse
from fastapi import Query, Form
from datetime import datetime, date
from fastapi.staticfiles import StaticFiles
from calendar import monthrange

app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
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
        matches = list({e[1] for e in employees if e[1].lower().startswith(prefix.lower())})
        return JSONResponse(matches[:10])
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

        return templates.TemplateResponse("landingPage.html", {
            "request": request,
            "employees": [(e[0], e[1], e[2]) for e in filtered]
        })

    except Exception as e:
        return HTMLResponse(content=f"Error: {e}", status_code=500)

@app.get("/dashboard", response_class=HTMLResponse)
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
            "employees": [(e[0], e[1], e[2]) for e in filtered]
        })

    except Exception as e:
        return HTMLResponse(content=f"Error: {e}", status_code=500)

def get_month_dates(year: int, month: int):
    days_in_month = monthrange(year, month)[1]
    return [date(year, month, day) for day in range(1, days_in_month + 1)]

@app.get("/employee/{emp_id}", response_class=HTMLResponse)
def view_employee(emp_id: int, request: Request):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT * FROM "18_EMPLOYEES_INFO" WHERE id = %s', (emp_id,))
        columns = [desc[0] for desc in cur.description]
        employee_data = cur.fetchone()
        employee = dict(zip(columns, employee_data))

        cur.execute('SELECT * FROM "18_ATTENDANCE" WHERE id = %s', (emp_id,))
        attendance = cur.fetchall()

        cur.execute('SELECT * FROM "18_LEAVE_TYPE" WHERE id = %s', (emp_id,))
        leaves = cur.fetchall()

        cur.close()
        conn.close()

        today = date.today()
        current_month_dates = get_month_dates(today.year, today.month)

        # Step 1: Map existing attendance
        attendance_map = {
            att[1].strftime('%Y-%m-%d'): 'present' if att[2].lower() == 'present' else 'absent'
            for att in attendance
        }

        # Step 2: Fill in missing dates (excluding weekends)
        for d in current_month_dates:
            d_str = d.strftime('%Y-%m-%d')
            is_weekend = d.weekday() in [5, 6]  # 5=Saturday, 6=Sunday

            if is_weekend:
                continue

            if d_str not in attendance_map:
                if d < today:
                    attendance_map[d_str] = 'absent'
                elif d == today:
                    attendance_map[d_str] = 'today'
                else:
                    attendance_map[d_str] = 'no data'

        return templates.TemplateResponse("employee.html", {
            "request": request,
            "employee": employee,
            "attendance": attendance,
            "leaves": leaves,
            "current_month_dates": current_month_dates,
            "attendance_map": attendance_map,
            "month_name": today.strftime("%B"),
            "year": today.year
        })

    except Exception as e:
        return HTMLResponse(content=f"Error: {e}", status_code=500)

@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT * FROM "18_CREDENTIALS" WHERE username = %s AND password = %s', (username, password))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            return RedirectResponse(url=f"/employee-home/{username}", status_code=303)
        else:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Invalid username or password"
            })

    except Exception as e:
        return HTMLResponse(content=f"Error: {e}", status_code=500)

@app.get("/employee-home/{username}", response_class=HTMLResponse)
def employee_home(request: Request, username: str, message: str = ""):
    return templates.TemplateResponse("employee_home.html", {
        "request": request,
        "username": username,
        "message": message
    })

@app.post("/checkin", response_class=HTMLResponse)
def checkin(request: Request, username: str = Form(...)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT id FROM "18_CREDENTIALS" WHERE username = %s', (username,))
        result = cur.fetchone()
        if not result:
            return HTMLResponse(content="Invalid user", status_code=400)

        emp_id = result[0]
        today = date.today()
        now = datetime.now()

        cur.execute('SELECT * FROM "18_ATTENDANCE" WHERE id = %s AND date = %s', (emp_id, today))
        existing = cur.fetchone()

        if existing:
            cur.close()
            conn.close()
            return RedirectResponse(
                url=f"/employee-home/{username}?message=You have already checked in today",
                status_code=302
            )

        cur.execute('INSERT INTO "18_ATTENDANCE" (date, id, status, check_in, check_out) VALUES (%s, %s, %s, %s, %s)',
                    (today, emp_id, 'present', now, None))

        conn.commit()
        cur.close()
        conn.close()

        return RedirectResponse(url=f"/employee-home/{username}?message=Check-in successful", status_code=302)

    except Exception as e:
        return HTMLResponse(content=f"Error: {e}", status_code=500)

@app.post("/checkout", response_class=HTMLResponse)
def checkout(request: Request, username: str = Form(...)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT id FROM "18_CREDENTIALS" WHERE username = %s', (username,))
        result = cur.fetchone()
        if not result:
            return HTMLResponse(content="Invalid user", status_code=400)

        emp_id = result[0]
        now = datetime.now()
        today = date.today()

        cur.execute('UPDATE "18_ATTENDANCE" SET check_out = %s WHERE id = %s AND date = %s AND check_out IS NULL',
                    (now, emp_id, today))

        conn.commit()
        cur.close()
        conn.close()

        return RedirectResponse(url=f"/employee-home/{username}?message=Check-out successful", status_code=302)

    except Exception as e:
        return HTMLResponse(content=f"Error: {e}", status_code=500)