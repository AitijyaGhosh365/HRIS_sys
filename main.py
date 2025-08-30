from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import psycopg2
from functools import lru_cache
from fastapi.responses import JSONResponse
from fastapi import Query
from fastapi import FastAPI, Request, Form
from datetime import datetime, date
import random
import string
from fastapi import Form
from fastapi import UploadFile
import shutil
import os



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
    
@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if username + password match
        cur.execute('SELECT * FROM "18_CREDENTIALS" WHERE username = %s AND password = %s', (username, password))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            # Redirect to welcome page with username
            response = RedirectResponse(url=f"/employee-home/{username}", status_code=303)
            return response
        else:
            # Invalid login
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


from geopy.geocoders import Nominatim

@app.post("/checkin", response_class=HTMLResponse)
def checkin(request: Request, username: str = Form(...),
            latitude: str = Form(...), longitude: str = Form(...)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get employee ID
        cur.execute('SELECT id FROM "18_CREDENTIALS" WHERE username = %s', (username,))
        result = cur.fetchone()
        if not result:
            return HTMLResponse(content="Invalid user", status_code=400)
        
        emp_id = result[0]
        today = date.today()
        now = datetime.now()

        # Check if already checked-in today
        cur.execute("""
            SELECT * FROM "18_ATTENDANCE"
            WHERE id = %s AND date = %s
        """, (emp_id, today))
        existing = cur.fetchone()
        if existing:
            cur.close()
            conn.close()
            return RedirectResponse(
                url=f"/employee-home/{username}?message=You have already checked in today",
                status_code=302
            )

        # Reverse geocoding
    
        geolocator = Nominatim(user_agent="employee_portal")
        
        try:
            location_obj = geolocator.reverse(f"{latitude},{longitude}", exactly_one=True)
            location_text = location_obj.address if location_obj else f"{latitude},{longitude}"
        except Exception:
            location_text = f"{latitude},{longitude}"


        

        # Insert new attendance record
        cur.execute("""
            INSERT INTO "18_ATTENDANCE" 
            (date, id, status, check_in, check_out, checkin_location, checkout_location)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (today, emp_id, 'present', now, None, location_text, None))

        conn.commit()
        cur.close()
        conn.close()

        return RedirectResponse(
            url=f"/employee-home/{username}?message=Check-in successful at {location_text}",
            status_code=302
        )

    except Exception as e:
        return HTMLResponse(content=f"Error: {e}", status_code=500)



@app.post("/checkout", response_class=HTMLResponse)
def checkout(request: Request, username: str = Form(...),
             latitude: str = Form(...), longitude: str = Form(...)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get employee ID
        cur.execute('SELECT id FROM "18_CREDENTIALS" WHERE username = %s', (username,))
        result = cur.fetchone()
        if not result:
            return HTMLResponse(content="Invalid user", status_code=400)
        
        emp_id = result[0]
        now = datetime.now()
        today = date.today()

        # Reverse geocoding
        geolocator = Nominatim(user_agent="employee_portal")
        location_obj = geolocator.reverse(f"{latitude},{longitude}", exactly_one=True)
        location_text = location_obj.address if location_obj else f"{latitude},{longitude}"

        # Update existing attendance row with checkout
        cur.execute("""
            UPDATE "18_ATTENDANCE"
            SET check_out = %s, checkout_location = %s
            WHERE id = %s AND date = %s AND check_out IS NULL
        """, (now, location_text, emp_id, today))

        conn.commit()
        cur.close()
        conn.close()

        return RedirectResponse(
            url=f"/employee-home/{username}?message=Check-out successful at {location_text}",
            status_code=302
        )

    except Exception as e:
        return HTMLResponse(content=f"Error: {e}", status_code=500)

def get_next_employee_id():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT MAX(id) FROM "18_EMPLOYEES_INFO"')
    last_id = cur.fetchone()[0]
    cur.close()
    conn.close()
    if last_id is None:
        return 1000001
    return last_id + 1

def generate_random_password(length=8):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))

@app.get("/admin/add-employee", response_class=HTMLResponse)
def add_employee_form(request: Request):
    next_id = get_next_employee_id()
    return templates.TemplateResponse("add_employee.html", {
        "request": request,
        "next_id": next_id
    })

@app.post("/admin/add-employee", response_class=HTMLResponse)
def add_employee_submit(
    request: Request,
    first_name: str = Form(...),
    middle_name: str = Form(None),
    last_name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(None),
    dept_id: str = Form(None),
    hire_date: str = Form(...),
    exit_date: str = Form(None),
    job_title: str = Form(...),
    ctc: float = Form(...),
    allowances: float = Form(0),
    field3: float = Form(0),
    field4: float = Form(0),
    status: str = Form('Active'),
    role: str = Form('User'),
    dob: str = Form(None)
):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        emp_id = get_next_employee_id()
        total_salary = ctc + allowances + field3 + field4
        password = generate_random_password()

        # Convert empty strings to None for optional date fields
        exit_date = exit_date if exit_date else None
        dob = dob if dob else None

        # Determine status automatically
        if exit_date:
            exit_dt = datetime.strptime(exit_date, "%Y-%m-%d").date()
            today = date.today()
            if exit_dt > today:
                status = "Resigned"
            else:
                status = "Inactive"
        else:
            status = "Active"

        # Insert into employees info
        cur.execute("""
            INSERT INTO "18_EMPLOYEES_INFO"
            (id, first_name, middle_name, last_name, email, phone_number, dept_id, hire_date,
             exit_date, job_title, salary, salary_allowances, salary_field3, salary_field4,
             status, role, dob)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            emp_id, first_name, middle_name, last_name, email, phone_number, dept_id, hire_date,
            exit_date, job_title, total_salary, allowances, field3, field4,  status, role, dob
        ))

        # Insert credentials
        cur.execute("""
            INSERT INTO "18_CREDENTIALS" (id, username, password)
            VALUES (%s, %s, %s)
        """, (emp_id, email, password))

        conn.commit()
        cur.close()
        conn.close()

        return templates.TemplateResponse("add_employee.html", {
            "request": request,
            "next_id": get_next_employee_id(),
            "success": f"Employee {first_name} {last_name} added successfully! Generated password: {password}"
        })

    except Exception as e:
        return HTMLResponse(content=f"Error: {e}", status_code=500)
    
@app.get("/admin/edit-employee/{emp_id}", response_class=HTMLResponse)
def edit_employee_form(request: Request, emp_id: int):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT * FROM "18_EMPLOYEES_INFO" WHERE id = %s', (emp_id,))
        columns = [desc[0] for desc in cur.description]
        employee_data = cur.fetchone()

        if not employee_data:
            return HTMLResponse(content="Employee not found", status_code=404)

        employee = dict(zip(columns, employee_data))
        cur.close()
        conn.close()

        return templates.TemplateResponse("edit_employee.html", {
            "request": request,
            "employee": employee
        })
    except Exception as e:
        return HTMLResponse(content=f"Error: {e}", status_code=500)

@app.post("/admin/edit-employee/{emp_id}", response_class=HTMLResponse)
def edit_employee_submit(
    request: Request,
    emp_id: int,
    first_name: str = Form(...),
    middle_name: str = Form(None),
    last_name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(None),
    dept_id: str = Form(None),
    hire_date: str = Form(...),
    exit_date: str = Form(None),
    job_title: str = Form(...),
    ctc: float = Form(...),
    allowances: float = Form(0),
    field3: float = Form(0),
    field4: float = Form(0),
    status: str = Form('Active'),
    role: str = Form('User'),
    dob: str = Form(None)
):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Convert empty strings to None
        exit_date = exit_date or None
        dob = dob or None

        # Determine status automatically
        if exit_date:
            exit_dt = datetime.strptime(exit_date, "%Y-%m-%d").date()
            today = date.today()
            if exit_dt > today:
                status = "Resigned"
            else:
                status = "Inactive"
        else:
            status = "Active"
        total_salary = ctc + allowances + field3 + field4
        cur.execute("""
            UPDATE "18_EMPLOYEES_INFO"
            SET first_name = %s, middle_name = %s, last_name = %s, email = %s,
                phone_number = %s, dept_id = %s, hire_date = %s, exit_date = %s,
                job_title = %s, Salary = %s, salary_allowances = %s,
                salary_field3 = %s, salary_field4 = %s, status = %s, role = %s, dob = %s
            WHERE id = %s
        """, (
            first_name, middle_name, last_name, email, phone_number, dept_id, hire_date,
            exit_date, job_title, total_salary, allowances, field3, field4, status, role, dob, emp_id
        ))

        conn.commit()
        cur.close()
        conn.close()

        # Refresh employee cache
        get_all_employees_cached.cache_clear()

        return RedirectResponse(
            url=f"/employee/{emp_id}",
            status_code=303
        )

    except Exception as e:
        return HTMLResponse(content=f"Error: {e}", status_code=500)
'''    
from fastapi import FastAPI, Request, Form, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
import shutil
import os
    
UPLOAD_DIR = "uploads/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/employee-details/{username}", response_class=HTMLResponse)
def employee_details_form(username: str, request: Request):
    # Lookup employee id
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, profile_pic FROM "18_EMPLOYEES_INFO" WHERE email = %s', (username,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if not result:
        return HTMLResponse(content="User not found", status_code=404)

    emp_id, profile_pic = result

    return templates.TemplateResponse(
        "employee_details_form.html",
        {"request": request, "emp_id": emp_id, "username": username, "profile_pic": profile_pic}
    )

# --- POST form ---
@app.post("/employee-details/{username}")
async def save_employee_details(
    username: str,
    # Previous Job
    company_name: str = Form(None),
    role: str = Form(None),
    salary: float = Form(None),
    join_date: str = Form(None),
    end_date: str = Form(None),
    # Education
    level: str = Form(None),
    school_or_college: str = Form(None),
    board_or_university: str = Form(None),
    degree_name: str = Form(None),
    marks: float = Form(None),
    marksheet: UploadFile = File(None),
    # Profile picture
    profile_pic: UploadFile = File(None)
):
    conn = get_db_connection()
    cur = conn.cursor()

    # Get employee ID from username
    cur.execute('SELECT id FROM "18_EMPLOYEES_INFO" WHERE email = %s', (username,))
    result = cur.fetchone()
    if not result:
        cur.close()
        conn.close()
        return HTMLResponse(content="User not found", status_code=404)

    emp_id = result[0]

    # --- Previous Job ---
    if company_name and role:
        cur.execute("""
            INSERT INTO previous_jobs (employee_id, company_name, role, salary, join_date, end_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (emp_id, company_name, role, salary, join_date, end_date))

    # --- Education ---
    marksheet_path = None
    if marksheet:
        marksheet_path = os.path.join(UPLOAD_DIR, marksheet.filename)
        with open(marksheet_path, "wb") as f:
            shutil.copyfileobj(marksheet.file, f)

    if level and school_or_college:
        cur.execute("""
            INSERT INTO education (employee_id, level, school_or_college, board_or_university, degree_name, marks, marksheet_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (emp_id, level, school_or_college, board_or_university, degree_name, marks, marksheet_path))

    # --- Profile Picture ---
    if profile_pic:
        profile_pic_path = os.path.join(UPLOAD_DIR, profile_pic.filename)
        with open(profile_pic_path, "wb") as f:
            shutil.copyfileobj(profile_pic.file, f)

        cur.execute("""
            UPDATE "18_EMPLOYEES_INFO" SET profile_pic = %s WHERE id = %s
        """, (profile_pic_path, emp_id))

    conn.commit()
    cur.close()
    conn.close()

    return RedirectResponse(url=f"/employee-home/{username}", status_code=303)
'''
