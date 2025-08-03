import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("SUPABASE_HOST"),
    port=os.getenv("SUPABASE_PORT"),
    database=os.getenv("SUPABASE_DATABASE"),
    user=os.getenv("SUPABASE_USER"),
    password=os.getenv("SUPABASE_PASSWORD")
)
cur = conn.cursor()

cur.execute('SELECT * FROM "COMPANY_INFO";')
rows = cur.fetchall()

for row in rows:
    print(row)

cur.close()
conn.close()
