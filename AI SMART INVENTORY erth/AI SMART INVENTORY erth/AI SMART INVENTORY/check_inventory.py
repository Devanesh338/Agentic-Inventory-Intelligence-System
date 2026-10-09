import database
try:
    with database.get_db_cursor() as c:
        c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='inventory'")
        print(c.fetchall())
except Exception as e:
    print(e)
