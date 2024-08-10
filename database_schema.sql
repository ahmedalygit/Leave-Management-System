-- SQL script to set up the database schema

-- Create Users table
CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT CHECK(role IN ('Employee', 'Manager')) NOT NULL,
    manager_id INTEGER,
    FOREIGN KEY (manager_id) REFERENCES Users (user_id)
);

-- Create LeaveRequests table
CREATE TABLE IF NOT EXISTS LeaveRequests (
    leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    leave_type TEXT NOT NULL,
    application_date DATE NOT NULL,
    comment TEXT,
    status TEXT CHECK(status IN ('Approved', 'Rejected', 'Waiting')) DEFAULT 'Waiting',
    FOREIGN KEY (user_id) REFERENCES Users (user_id)
);
