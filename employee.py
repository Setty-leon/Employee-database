import streamlit as st
import json
import os
import random
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import streamlit_authenticator as stauth
import bcrypt

# File paths
DB_FILE = "employee_database.json"
RATES_FILE = "hourly_rates.json"

# Load or initialize employee database
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        employee_db = json.load(f)
else:
    employee_db = {}

# Load or initialize hourly rates
default_rates = {"Ordinary Staff": 10, "Supervisor": 15, "Admin": 20}
if os.path.exists(RATES_FILE):
    with open(RATES_FILE, "r") as f:
        hourly_rates = json.load(f)
else:
    hourly_rates = default_rates.copy()

# Save functions
def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(employee_db, f, indent=4)

def save_rates():
    with open(RATES_FILE, "w") as f:
        json.dump(hourly_rates, f, indent=4)

# Generate unique 4-digit employee number
def generate_employee_number():
    while True:
        num = str(random.randint(1000, 9999))
        if num not in employee_db:
            return num

# Validate input fields
def validate_inputs(name, dob, id_number, age, department):
    if not name or not department:
        return "Name and Department cannot be empty."
    try:
        datetime.strptime(dob, "%Y-%m-%d")
    except ValueError:
        return "Date of Birth must be in YYYY-MM-DD format."
    if not id_number.isalnum():
        return "ID/Passport number must be alphanumeric."
    if not age.isdigit() or not (18 <= int(age) <= 100):
        return "Age must be a number between 18 and 100."
    return None

# Calculate salary
def calculate_salary(hours, rate, overtime=0, deductions=0):
    return round((hours + overtime) * rate - deductions, 2)

# Add salary history
def update_salary_history(emp_num, salary):
    now = datetime.now()
    month = now.strftime("%Y-%m")
    if "Salary History" not in employee_db[emp_num]:
        employee_db[emp_num]["Salary History"] = {}
    employee_db[emp_num]["Salary History"][month] = salary

# Generate payslip PDF
def generate_payslip_pdf(emp_num, month):
    emp = employee_db[emp_num]
    salary_info = emp["Salary History"].get(month, None)
    if not salary_info:
        return None

    filename = f"payslip_{emp_num}_{month}.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, f"Payslip for {emp['Name']} - {month}")
    c.drawString(100, 730, f"Employee Number: {emp_num}")
    c.drawString(100, 710, f"Role: {emp['Role']}")
    c.drawString(100, 690, f"Department: {emp['Department']}")
    c.drawString(100, 670, f"Hours Worked: {emp['Hours Worked']}")
    c.drawString(100, 650, f"Hourly Rate: {hourly_rates[emp['Role']]}")
    c.drawString(100, 630, f"Overtime: {emp.get('Overtime', 0)}")
    c.drawString(100, 610, f"Deductions: {emp.get('Deductions', 0)}")
    c.drawString(100, 590, f"Final Salary: {salary_info}")
    c.save()
    return filename

# --- AUTHENTICATION SETUP ---
names = ['Setty Ncube', 'Admin']
usernames = ['setty', 'admin']
passwords = ['mypassword', 'admin123']

# Hash passwords
hashed_passwords = [bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode() for pw in passwords]


authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
                                    'employee_app', 'abcdef', cookie_expiry_days=30)

name, authentication_status, username = authenticator.login('Login', 'main')

# --- LOGIN LOGIC ---
if authentication_status:
    st.success(f"Welcome {name}!")
    st.title("Employee Management App")
    # ✅ Place your existing app code BELOW this block
elif authentication_status == False:
    st.error("Username or password is incorrect")
elif authentication_status == None:
    st.warning("Please enter your username and password")
# Login system
def login():
    st.sidebar.title("Login")
    role = st.sidebar.selectbox("Login as", ["Admin", "Employee"])
    if role == "Admin":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            if (username == "admin" and password == "admin123") or (username == "manager" and password == "mgr2024"):
                return "Admin", username
            else:
                st.sidebar.error("Invalid admin credentials.")
    else:
        emp_num = st.sidebar.text_input("Employee Number")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            if emp_num in employee_db and employee_db[emp_num].get("Password") == password:
                return "Employee", emp_num
            else:
                st.sidebar.error("Invalid employee credentials.")
    return None, None

# Admin interface
def admin_interface():
    st.title("Admin Dashboard")

    menu = st.sidebar.radio("Menu", ["Add Employee", "Edit Employee", "View Employee", "Export to Excel", "Update Hourly Rates", "Employee Count", "Generate Payslip"])

    if menu == "Add Employee":
        st.subheader("Add New Employee")
        name = st.text_input("Name")
        dob = st.text_input("Date of Birth (YYYY-MM-DD)")
        id_number = st.text_input("ID/Passport Number")
        age = st.text_input("Age")
        department = st.text_input("Department")
        role = st.selectbox("Role", list(hourly_rates.keys()))
        work_type = st.selectbox("Work Type", ["Hours", "Days"])
        work_value = st.number_input("Enter number of hours or days", min_value=0)
        overtime = st.number_input("Overtime Hours", min_value=0)
        deductions = st.number_input("Deductions", min_value=0.0)
        password = st.text_input("Set Employee Password")

        if st.button("Add Employee"):
            error = validate_inputs(name, dob, id_number, age, department)
            if error:
                st.error(error)
            else:
                emp_num = generate_employee_number()
                hours = work_value if work_type == "Hours" else work_value * 12
                rate = hourly_rates[role]
                salary = calculate_salary(hours, rate, overtime, deductions)
                employee_db[emp_num] = {
                    "Name": name,
                    "Date of Birth": dob,
                    "ID/Passport": id_number,
                    "Age": age,
                    "Department": department,
                    "Role": role,
                    "Hours Worked": hours,
                    "Overtime": overtime,
                    "Deductions": deductions,
                    "Password": password
                }
                update_salary_history(emp_num, salary)
                save_db()
                st.success(f"Employee added with number: {emp_num}")

    elif menu == "Edit Employee":
        st.subheader("Edit Employee")
        emp_num = st.text_input("Enter Employee Number")
        if emp_num in employee_db:
            emp = employee_db[emp_num]
            name = st.text_input("Name", emp["Name"])
            dob = st.text_input("Date of Birth", emp["Date of Birth"])
            id_number = st.text_input("ID/Passport", emp["ID/Passport"])
            age = st.text_input("Age", emp["Age"])
            department = st.text_input("Department", emp["Department"])
            role = st.selectbox("Role", list(hourly_rates.keys()), index=list(hourly_rates.keys()).index(emp["Role"]))
            hours = st.number_input("Hours Worked", value=emp["Hours Worked"])
            overtime = st.number_input("Overtime Hours", value=emp.get("Overtime", 0))
            deductions = st.number_input("Deductions", value=emp.get("Deductions", 0.0))

            if st.button("Update"):
                error = validate_inputs(name, dob, id_number, age, department)
                if error:
                    st.error(error)
                else:
                    emp.update({
                        "Name": name,
                        "Date of Birth": dob,
                        "ID/Passport": id_number,
                        "Age": age,
                        "Department": department,
                        "Role": role,
                        "Hours Worked": hours,
                        "Overtime": overtime,
                        "Deductions": deductions
                    })
                    salary = calculate_salary(hours, hourly_rates[role], overtime, deductions)
                    update_salary_history(emp_num, salary)
                    save_db()
                    st.success("Employee updated.")
        elif emp_num:
            st.error("Employee not found.")

    elif menu == "View Employee":
        st.subheader("View Employee")
        emp_num = st.text_input("Enter Employee Number")
        if emp_num in employee_db:
            st.json(employee_db[emp_num])
        elif emp_num:
            st.error("Employee not found.")

    elif menu == "Export to Excel":
        st.subheader("Export All Employees to Excel")
        if st.button("Export"):
            df = pd.DataFrame.from_dict(employee_db, orient="index")
            df.to_excel("employee_data.xlsx", engine="openpyxl")
            with open("employee_data.xlsx", "rb") as f:
                st.download_button("Download Excel", f, file_name="employee_data.xlsx")

    elif menu == "Update Hourly Rates":
        st.subheader("Update Hourly Rates")
        for role in hourly_rates:
            new_rate = st.number_input(f"{role} Rate", value=hourly_rates[role])
            hourly_rates[role] = new_rate
        if st.button("Save Rates"):
            save_rates()
            st.success("Rates updated.")

    elif menu == "Employee Count":
        st.subheader("Total Employees")
        st.write(f"Total: {len(employee_db)}")

    elif menu == "Generate Payslip":
        st.subheader("Generate Payslip")
        emp_num = st.text_input("Employee Number")
        if emp_num in employee_db:
            months = list(employee_db[emp_num].get("Salary History", {}).keys())
            if months:
                month = st.selectbox("Select Month", months)
                if st.button("Generate PDF"):
                    pdf_file = generate_payslip_pdf(emp_num, month)
                    if pdf_file:
                        with open(pdf_file, "rb") as f:
                            st.download_button("Download Payslip PDF", f, file_name=pdf_file)
                    else:
                        st.error("No salary data for selected month.")
            else:
                st.info("No salary history available.")
        elif emp_num:
            st.error("Employee not found.")

# Employee interface
def employee_interface(emp_num):
    st.title("Employee Dashboard")
    emp = employee_db[emp_num]
    st.subheader("Your Information")
    st.json(emp)

    st.subheader("Salary History")
    history = emp.get("Salary History", {})
    if history:
        df = pd.DataFrame(list(history.items()), columns=["Month", "Salary"])
        st.table(df)
    else:
        st.info("No salary history available.")

    st.subheader("Download Payslip")
    months = list(history.keys())
    if months:
        month = st.selectbox("Select Month", months)
        if st.button("Download PDF"):
            pdf_file = generate_payslip_pdf(emp_num, month)
            if pdf_file:
                with open(pdf_file, "rb") as f:
                    st.download_button("Download Payslip PDF", f, file_name=pdf_file)
    else:
        st.info("No payslips available.")

    st.subheader("Reset Password")
    new_pass = st.text_input("New Password", type="password")
    if st.button("Update Password"):
        employee_db[emp_num]["Password"] = new_pass
        save_db()
        st.success("Password updated.")

# Main app
def main():
    role, user = login()
    if role == "Admin":
        admin_interface()
    elif role == "Employee":
        employee_interface(user)

if __name__ == "__main__":

    main()




