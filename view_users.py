import sqlite3

def view_users():
    conn = sqlite3.connect('leave_management.db')
    c = conn.cursor()
    c.execute("SELECT * FROM Users")
    users = c.fetchall()
    conn.close()

    for user in users:
        print(user)

if __name__ == "__main__":
    view_users()
