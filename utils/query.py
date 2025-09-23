from config.db_connection import get_connection

def get_all_users():
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("Select id,name from users")
    users=cursor.fetchall()
    conn.close()
    print(users)


get_all_users()
