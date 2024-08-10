import streamlit as st
import sqlite3  # or use mysql.connector for MySQL
from datetime import datetime

# Database setup and connection
def create_connection():
    conn = sqlite3.connect('leave_management.db')
    return conn

def setup_database():
    conn = create_connection()
    c = conn.cursor()

    # Create Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('Employee', 'Manager')) NOT NULL,
            manager_id INTEGER,
            FOREIGN KEY (manager_id) REFERENCES Users (user_id)
        )
    ''')

    # Create LeaveRequests table
    c.execute('''
        CREATE TABLE IF NOT EXISTS LeaveRequests (
            leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            leave_type TEXT NOT NULL,
            application_date DATE NOT NULL,
            comment TEXT,
            status TEXT CHECK(status IN ('Approved', 'Rejected', 'Waiting')) DEFAULT 'Waiting',
            FOREIGN KEY (user_id) REFERENCES Users (user_id)
        )
    ''')

    conn.commit()
    conn.close()

# Authentication and User Role Management
def signup_user(name, email, password, role, manager_id=None):
    try:
        conn = create_connection()
        c = conn.cursor()

        # Debugging: Check the values being inserted
        st.write(f"Inserting user: {name}, {email}, {password}, {role}, manager_id: {manager_id}")

        # Ensure manager_id is None if role is Manager
        if role == "Manager":
            manager_id = None

        # Execute the insertion
        c.execute("INSERT INTO Users (name, email, password, role, manager_id) VALUES (?, ?, ?, ?, ?)",
                  (name, email, password, role, manager_id))
        conn.commit()
        conn.close()

        st.success("User successfully signed up!")
    except sqlite3.ProgrammingError as e:
        st.error(f"An error occurred: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

def login_user(email, password):
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT user_id, role FROM Users WHERE email=? AND password=?", (email, password))
    user = c.fetchone()
    conn.close()
    return user

def get_manager_name(manager_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM Users WHERE user_id=?", (manager_id,))
    result = c.fetchone()
    conn.close()

    if result:
        return result[0]
    else:
        return None

# Logout Function
def logout():
    # Clear the session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    # Redirect to the login page
    st.experimental_set_query_params(page="login")
    st.success("You have been logged out. Redirecting to the login page...")


# Employee Page
def employee_page():
    if 'user_id' not in st.session_state or 'role' not in st.session_state:
        st.error("Session expired or not logged in. Please log in again.")
        st.stop()

    employee_id = st.session_state['user_id']
    conn = create_connection()
    c = conn.cursor()

    # Fetch employee name and manager_id
    c.execute("SELECT name, manager_id FROM Users WHERE user_id=?", (employee_id,))
    employee_name, manager_id = c.fetchone()

    if manager_id:
        manager_name = get_manager_name(manager_id)
    else:
        manager_name = "No Manager Assigned"

    st.title(f"Welcome {employee_name}")
    st.header("Apply for Leave")

    # Apply for leave logic
    leave_type = st.selectbox("Select Leave Type", ["Personal", "Sick", "Official"])
    comment = st.text_area("Leave Comment")
    if st.button("Apply for Leave"):
        application_date = datetime.now().strftime("%Y-%m-%d")
        c.execute('''
            INSERT INTO LeaveRequests (user_id, leave_type, application_date, comment)
            VALUES (?, ?, ?, ?)
        ''', (employee_id, leave_type, application_date, comment))
        conn.commit()
        st.success("Leave application submitted successfully!")

    # Display leave requests
    st.header("Your Leave Requests")
    c.execute('''
        SELECT application_date, leave_type, comment, status
        FROM LeaveRequests WHERE user_id = ?
    ''', (employee_id,))
    leave_requests = c.fetchall()

    if leave_requests:
        leave_table = {
            "Date of Application": [req[0] for req in leave_requests],
            "Leave Type": [req[1] for req in leave_requests],
            "Manager Name": [manager_name for _ in leave_requests],
            "Comment": [req[2] for req in leave_requests],
            "Status": [req[3] for req in leave_requests],
        }
        st.table(leave_table)
    else:
        st.info("No leave requests found.")

    if st.button("Logout"):
        logout()

    conn.close()

# Manager Dashboard
def manager_dashboard():
    if 'user_id' not in st.session_state or 'role' not in st.session_state:
        st.error("Session expired or not logged in. Please log in again.")
        st.stop()

    manager_id = st.session_state['user_id']

    st.title("Manager Dashboard")
    conn = create_connection()
    c = conn.cursor()

    c.execute('''
        SELECT LeaveRequests.leave_id, Users.name, LeaveRequests.leave_type, LeaveRequests.application_date, LeaveRequests.comment, LeaveRequests.status 
        FROM LeaveRequests 
        JOIN Users ON LeaveRequests.user_id = Users.user_id 
        WHERE Users.manager_id=? AND LeaveRequests.status='Waiting'
    ''', (manager_id,))
    leave_requests = c.fetchall()

    if leave_requests:
        # Create a table to display the leave requests
        leave_table = {
            "Leave ID": [req[0] for req in leave_requests],
            "Employee Name": [req[1] for req in leave_requests],
            "Leave Type": [req[2] for req in leave_requests],
            "Date of Application": [req[3] for req in leave_requests],
            "Comment": [req[4] for req in leave_requests],
            "Status": [req[5] for req in leave_requests],
        }
        st.table(leave_table)

        # Approve/Reject buttons
        for leave_id in leave_table["Leave ID"]:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Approve", key=f"approve_{leave_id}_manager_{manager_id}"):
                    c.execute("UPDATE LeaveRequests SET status='Approved' WHERE leave_id=?", (leave_id,))
                    conn.commit()
                    st.success(f"Leave request {leave_id} approved")
            with col2:
                if st.button("Reject", key=f"reject_{leave_id}_manager_{manager_id}"):
                    c.execute("UPDATE LeaveRequests SET status='Rejected' WHERE leave_id=?", (leave_id,))
                    conn.commit()
                    st.error(f"Leave request {leave_id} rejected")

    else:
        st.info("No leave requests to review.")

    if st.button("Logout"):
        logout()

    conn.close()

# Main Application
import streamlit as st

def main():
    st.title("Streamlit Leave Management System")
    setup_database()

    # Check the query parameters
    query_params = st.experimental_get_query_params()
    page = query_params.get("page", ["home"])[0]

    # Check if the user is already logged in
    if 'user_id' in st.session_state and 'role' in st.session_state:
        if st.session_state.role == "Employee":
            employee_page()
        elif st.session_state.role == "Manager":
            manager_dashboard()
    else:
        # Display the login page automatically if redirected after logout
        if page == "login":
            st.experimental_set_query_params()  # Clear the query params after redirect
            show_login_page()
        else:
            menu = ["Home", "Sign Up", "Login"]
            choice = st.sidebar.selectbox("Menu", menu, key="main_menu")

            if choice == "Home":
                st.subheader("Welcome to the Leave Management System")

            elif choice == "Sign Up":
                show_signup_page()

            elif choice == "Login":
                show_login_page()

def show_login_page():
    st.subheader("Login Section")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", key="login_button"):
        user = login_user(email, password)
        if user:
            user_id, role = user
            st.session_state.user_id = user_id  # Save user_id in session state
            st.session_state.role = role  # Save role in session state
        else:
            st.error("Incorrect email or password")

def show_signup_page():
    st.subheader("Create New Account")
    name = st.text_input("Name", key="signup_name")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    role = st.selectbox("Role", ["Employee", "Manager"], key="signup_role")

    manager_id = None
    if role == "Employee":
        conn = create_connection()
        c = conn.cursor()
        c.execute("SELECT user_id, name FROM Users WHERE role='Manager'")
        managers = c.fetchall()
        conn.close()

        if managers:
            selected_manager = st.selectbox("Select Manager", options=managers, format_func=lambda x: x[1], key="signup_manager")
            manager_id = selected_manager[0]  # Extract the manager's user_id (which is an integer)
        else:
            st.warning("No managers available. Please sign up as a manager first.")

    if st.button("Sign Up", key="signup_button"):
        if role == "Employee" and manager_id is None:
            st.error("Please select a manager.")
        else:
            signup_user(name, email, password, role, manager_id)
            
if __name__ == '__main__':
    main()
