import sqlite3


def create_connection():
    conn = sqlite3.connect('leave_management.db')
    return conn


def delete_all_records():
    conn = create_connection()
    c = conn.cursor()

    # Delete all records from the Users and LeaveRequests tables
    c.execute("DELETE FROM Users;")
    c.execute("DELETE FROM LeaveRequests;")

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


if __name__ == "__main__":
    delete_all_records()
    print("All records deleted successfully.")
