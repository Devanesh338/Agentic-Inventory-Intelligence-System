import database
try:
    with database.get_db_cursor() as c:
        c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        print(c.fetchall())
except Exception as e:
    print(e)
