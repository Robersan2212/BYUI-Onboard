import contextlib
import io
import traceback
import bcrypt
from bson import ObjectId
import streamlit as st
from datetime import datetime
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.database import (
    get_all_notes,
    add_new_hire,
    get_new_hires_count,
    get_offboarding_tasks,
    get_recent_hires_with_tasks,
    get_recent_hires,
    get_offboards_count,
    get_completed_onboardings_count,
    get_monthly_hires_data,
    reset_offboard_table,
    search_employee,
    get_onboarding_tasks,
    remove_hire,
    update_task_status,
    get_employee_tasks,
    update_onboarding_tasks,
    get_access_control_task,
    save_user_state,
    get_user_state,
    create_user,
    verify_user,
    create_note,
    get_all_notes,
    delete_note,
    update_note,
    update_offboard_count,
    db,
    create_signup_request,
    get_pending_signup_requests,
    approve_signup_request,
    deny_signup_request,
    get_all_trainers, 
    delete_user,
    mark_employee_completed
)
st.markdown(
    """
    <style>
    
    .css-1d391kg {
        background-color: #1565C0;
    }
    
    .css-1d391kg .e1fqkh3o1 {
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Initialize session state
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "role" not in st.session_state:
    st.session_state.role = None

# Available roles
ROLES = [ "IT Manager", "Trainer"]

def login_signup():
    st.title("Onboarding 🚂")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.header("Login")
        with st.form(key='login_form'):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Log in")
            
            if submit_button:
                user = verify_user(email, password)
                if user:
                    st.session_state.user_email = email
                    st.session_state.role = user['role']
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid email or password")

    with tab2:
        st.header("Sign Up")
        new_email = st.text_input("Email", key="new_email")
        new_password = st.text_input("Password", type="password", key="new_password")
        confirm_password = st.text_input("Confirm Password", type="password")
        role = st.selectbox("Role", ROLES)

        if role == "IT Manager":
            manager_code = st.text_input("Enter IT Manager Code", type="password")
        
        if st.button("Sign Up"):
            if new_password != confirm_password:
                st.error("Passwords do not match")
            elif not new_email or not new_password:
                st.error("Email and password are required")
            elif role == "IT Manager":
                if manager_code != st.secrets["IT_MANAGER_CODE"]:
                    st.error("Invalid IT Manager Code")
                else:
                    # Directly create the IT Manager account
                    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                    user_id = create_user(new_email, hashed_password, role)
                    if user_id:
                        st.success("IT Manager account created successfully! You can now log in.")
                    else:
                        st.error("Failed to create account. Please try again.")
            elif role == "Trainer":
                # Create a signup request for Trainers
                request_id = create_signup_request(new_email, new_password, role)
                if request_id:
                    st.success("Sign-up request submitted successfully! Please wait for IT Manager approval.")
                else:
                    st.error("Failed to submit sign-up request. Please try again.")
            else:
                st.error("Invalid role selected")

# Page definitions
def home():
    st.title("Employee Onboarding and Offboarding System 🖥️")
    display_dashboard()
    display_graphs()
    display_training_setup_progress()

def onboarding():
    
    if "new_hire_id" not in st.session_state:
        with st.form("new_hire_form"):
            st.subheader("New Hire Information")
            first_name = st.text_input("First Name", autocomplete="off")
            last_name = st.text_input("Last Name", autocomplete="off")
            email = st.text_input("BYU-I Email", autocomplete="off")
            i_number = st.text_input("I-number", autocomplete="off")
            date_of_birth = st.date_input("Date of Birth", min_value=datetime(1950, 1, 1))
            start_date = datetime.now()

            submitted = st.form_submit_button("Submit")
            if submitted:
                employee_id = add_new_hire(first_name, last_name, email, i_number, date_of_birth, start_date)
                st.success(f"New hire {first_name} {last_name} has been added successfully!")
                st.session_state.new_hire_id = str(employee_id)
                st.session_state.first_name = first_name
                st.session_state.last_name = last_name
                if "user_email" in st.session_state:
                    save_user_state(st.session_state.user_email, {
                        "new_hire_id": str(employee_id),
                        "first_name": first_name,
                        "last_name": last_name
                    })
                else:
                    st.warning("User email not found in session state. Unable to save user state.")
                st.rerun()
    else:
        st.subheader(f"Onboarding Tasks for {st.session_state.first_name} {st.session_state.last_name}")

        # Get access control tasks
        access_tasks = get_access_control_task()

        # Create checkboxes for each task
        updated_tasks = {}
        for task, value in access_tasks.items():
            if isinstance(value, dict) and 'url' in value:
                col1, col2 = st.columns([3, 1])
                with col1:
                    updated_tasks[task] = st.checkbox(task, value=value['status'])
                with col2:
                    st.markdown(f"[Go to site]({value['url']})")
            else:
                updated_tasks[task] = st.checkbox(task, value=value)

        # Add a Done button
        if st.button("Done"):
            # Update the tasks in the database
            update_onboarding_tasks(st.session_state.new_hire_id, updated_tasks)
            st.success("Onboarding tasks updated successfully!")

        # Clear the session state if needed
        if st.button("Start New Onboarding"):
            for key in ['new_hire_id', 'first_name', 'last_name']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # Training and Setup Process section
    st.subheader("Training and Setup Process  📈")
    employees = get_recent_hires_with_tasks()
    selected_employee = st.selectbox("Select Employee", 
                                     options=[f"{e['first_name']} {e['last_name']}" for e in employees],
                                     format_func=lambda x: x)
    
    if selected_employee:
        employee = next(e for e in employees if f"{e['first_name']} {e['last_name']}" == selected_employee)
        employee_id = str(employee['_id'])
        
        days = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "Day 8", "Day 9", "Day 10"]
        selected_day = st.selectbox("Select Day", options=days)
        
        tasks = get_onboarding_tasks()[selected_day]
        employee_tasks = get_employee_tasks(employee_id)
        
        for task in tasks:
            task_status = employee_tasks.get('tasks', {}).get(selected_day, {}).get(task, False)
            if st.checkbox(task, value=task_status, key=f"{employee_id}_{selected_day}_{task}"):
                update_task_status(employee_id, selected_day, task, True)
            else:
                update_task_status(employee_id, selected_day, task, False)
    

    # Recent Hires section
    st.subheader("Recent Hires 👥")
    recent_hires = get_recent_hires()
    if recent_hires:
        for hire in recent_hires:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"{hire['first_name']} {hire['last_name']} - Started on {hire['start_date'].strftime('%Y-%m-%d')}")
            with col2:
                if st.button("Remove", key=f"remove_{hire['_id']}"):
                    # Add confirmation dialog
                    if st.session_state.get(f"confirm_remove_{hire['_id']}", False):
                        if remove_hire(hire['_id']):
                            st.success(f"Removed {hire['first_name']} {hire['last_name']} from the system.")
                            st.session_state[f"confirm_remove_{hire['_id']}"] = False
                            st.rerun()
                        else:
                            st.error("Failed to remove the hire. Please try again.")
                    else:
                        st.warning(f"Are you sure you want to remove {hire['first_name']} {hire['last_name']}?")
            with col3:
                if st.button("Completed", key=f"complete_{hire['_id']}"):
                    if mark_employee_completed(hire['_id']):
                        st.success(f"Marked {hire['first_name']} {hire['last_name']} as completed.")
                        st.rerun()
                    else:
                        st.error("Failed to mark the hire as completed. Please try again.")
    else:
        st.write("No recent hires.")

def offboarding():
    st.header("Student Offboarding 👋")

    # Employee Search
    col1, col2 = st.columns(2)
    with col1:
        first_name = st.text_input("First Name")
    with col2:
        last_name = st.text_input("Last Name")
    
    if st.button("Search Employee"):
        if first_name and last_name:
            employee = search_employee(first_name, last_name)
            if employee:
                st.session_state.employee = employee
                st.success(f"Employee found: {employee['first_name']} {employee['last_name']}")
            else:
                st.error("Employee not found.")
        else:
            st.warning("Please enter both first and last name.")
    
    # Offboarding Process
    if 'employee' in st.session_state:
        employee = st.session_state.employee
        st.subheader(f"Offboarding: {employee['first_name']} {employee['last_name']}")

        offboarding_tasks = get_offboarding_tasks()
        
        for task, value in offboarding_tasks.items():
            if isinstance(value, dict):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.checkbox(task, key=f"offboarding_{task}")
                with col2:
                    st.markdown(f"[Go to site]({value['url']})")
            else:
                st.checkbox(task, key=f"offboarding_{task}")
        
        if st.button("Complete Offboarding"):
            try:
                employee_id = str(employee['_id'])
                
                # 1. Erase the employee from the database
                if remove_hire(employee_id):
                    st.success(f"Employee {employee['first_name']} {employee['last_name']} has been removed from the database.")
                    
                    # 2. Update offboard count (This will reflect in the dashboard)
                    update_offboard_count(datetime.now())
                    st.success("Offboard count has been updated.")
                    
                    # 3. Clear the session state (This will remove the employee from the onboarding page)
                    if 'employee' in st.session_state:
                        del st.session_state.employee
                    if 'new_hire_id' in st.session_state:
                        del st.session_state.new_hire_id
                    
                    st.success("Employee has been successfully offboarded and removed from all relevant pages.")
                    st.info("Please refresh the page to see the updated dashboard.")
                else:
                    st.error("Failed to remove the employee. Please try again.")
            except Exception as e:
                st.error(f"An error occurred during the offboarding process: {str(e)}")

    # Debug section
    st.subheader("Currrent Employee List 📋")
    if st.button("Show all employees in database"):
        all_employees = list(db.employees.find())
        st.write(f"Total employees in database: {len(all_employees)}")
        for emp in all_employees:
            st.write(f"{emp['first_name']} {emp['last_name']} - ID: {emp['_id']}")

def notes():
    # Note Creation
    st.subheader("Create a New Note ➕")
    with st.form("new_note_form"):
        title = st.text_input("Title")
        topic = st.text_input("Topic (optional)")
        content = st.text_area("Note Content")
        submitted = st.form_submit_button("Save Note")
        
        if submitted:
            if title and content:
                note_id = create_note(st.session_state.role, title, topic, content)
                save_user_state(st.session_state.user_email, {"last_note_id": str(note_id)})
                st.success("Note saved successfully!")
                st.rerun()
            else:
                st.error("Title and content are required.")

    # View All Notes
    st.subheader("All Notes 🗒️")
    notes = get_all_notes()
    
    for note in notes:
        with st.expander(f"{note['title']} - by {note['user']}"):
            st.write(f"**Topic:** {note['topic'] if note['topic'] else 'N/A'}")
            st.write(f"**Created at:** {note['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(note['content'])
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Edit", key=f"edit_{note['_id']}"):
                    st.session_state.editing_note = note
                    st.rerun()
            with col2:
                if st.button("Delete", key=f"delete_{note['_id']}"):
                    st.session_state.deleting_note = note['_id']
                    st.rerun()

        if st.session_state.get('deleting_note') == note['_id']:
            if st.button("Confirm Delete", key=f"confirm_delete_{note['_id']}"):
                try:
                    delete_note(note['_id'])
                    st.success("Note deleted successfully!")
                    del st.session_state.deleting_note
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete note: {str(e)}")
            if st.button("Cancel", key=f"cancel_delete_{note['_id']}"):
                del st.session_state.deleting_note
                st.rerun()

    # Edit Note Form
    if 'editing_note' in st.session_state:
        st.subheader("Edit Note")
        with st.form("edit_note_form"):
            edited_title = st.text_input("Title", value=st.session_state.editing_note['title'])
            edited_topic = st.text_input("Topic", value=st.session_state.editing_note['topic'])
            edited_content = st.text_area("Content", value=st.session_state.editing_note['content'])
            if st.form_submit_button("Update Note"):
                try:
                    update_note(st.session_state.editing_note['_id'], edited_title, edited_topic, edited_content)
                    st.success("Note updated successfully!")
                    del st.session_state.editing_note
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update note: {str(e)}")
        
        if st.button("Cancel Edit"):
            del st.session_state.editing_note
            st.rerun()

def admin():
    # Check if the user has the IT Manager role
    if st.session_state.role != "IT Manager":
        st.error("You don't have permission to access this page.")
        return

    st.header("Admin Panel 🔐")
    
    # Pending Signup Requests section
    st.subheader("Pending Signup Requests ⏳")
    
    pending_requests = get_pending_signup_requests()
    
    if pending_requests:
        for request in pending_requests:
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            with col1:
                st.write(f"Email: {request['email']}")
            with col2:
                st.write(f"Role: {request['role']}")
            with col3:
                if st.button("Approve", key=f"approve_{request['_id']}"):
                    if approve_signup_request(request['_id']):
                        st.success(f"Approved signup for: {request['email']}")
                        st.rerun()
                    else:
                        st.error("Failed to approve signup. Please try again.")
            with col4:
                if st.button("Deny", key=f"deny_{request['_id']}"):
                    if deny_signup_request(request['_id']):
                        st.success(f"Denied signup for: {request['email']}")
                        st.rerun()
                    else:
                        st.error("Failed to deny signup. Please try again.")
    else:
        st.write("No pending signup requests.")
    
    # Existing Manage Trainer Users section
    st.subheader("Manage Trainer Users 👥")
    
    trainers = get_all_trainers()
    
    if trainers:
        for trainer in trainers:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"Email: {trainer['email']}")
            with col2:
                st.write(f"Created: {trainer['created_at'].strftime('%Y-%m-%d')}")
            with col3:
                if st.button("Delete", key=f"delete_{trainer['_id']}"):
                    if delete_user(trainer['_id']):
                        st.success(f"Deleted trainer: {trainer['email']}")
                        st.rerun()
                    else:
                        st.error("Failed to delete trainer. Please try again.")
    else:
        st.write("No trainer users found.")
    
    st.subheader("Reset Offboard Table ⚠️")
    
    if "show_reset_confirmation" not in st.session_state:
        st.session_state.show_reset_confirmation = False

    if st.button("Reset Offboard Table"):
        st.session_state.show_reset_confirmation = True

    if st.session_state.show_reset_confirmation:
        st.warning("Are you sure you want to reset the offboard table? This action cannot be undone.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Reset"):
                if reset_offboard_table():
                    st.success("Offboard table has been reset successfully!")
                else:
                    st.error("Failed to reset offboard table. Please check the server logs.")
                st.session_state.show_reset_confirmation = False
        with col2:
            if st.button("Cancel"):
                st.session_state.show_reset_confirmation = False
                st.info("Reset operation cancelled.")

    # Debug Information section
    st.subheader("Debug Information 🔧")
    if st.button("Show current offboard state"):
        offboard_summary = db.summary.find_one({"_id": "offboard_summary"})
        offboard_count = db.offboards.count_documents({})

        st.write(f"Total offboards in summary: {offboard_summary.get('total_offboards', 0) if offboard_summary else 0}")
        st.write(f"Actual offboard records: {offboard_count}")

        if offboard_count > 0:
            st.write("Sample of 5 recent offboards:")
            for offboard in db.offboards.find().sort("date", -1).limit(5):
                st.write(f"Offboard ID: {offboard['_id']}, Date: {offboard.get('date', 'N/A')}")
        else:
            st.write("No offboard records found in the database.")

   
   

    


def login():
    st.header("Log in")
    username = st.text_input("Username")
    role = st.selectbox("Choose your role", ROLES)
    if st.button("Log in"):
        st.session_state.role = role
        st.session_state.username = username
        user_state = get_user_state(username)
        if user_state:
            st.session_state.update(user_state)
        st.rerun() 

def logout():
    save_user_state(st.session_state.user_email, dict(st.session_state))
    st.session_state.user_email = None
    st.session_state.role = None
    st.rerun()

# Helper functions for the home page
def display_dashboard():
    st.subheader("Dashboard")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="New Hires (Semester)", value=get_new_hires_count("semester"))
        st.metric(label="Offboards (Semester)", value=get_offboards_count("semester"))
    
    with col2:
        st.metric(label="New Hires (Month)", value=get_new_hires_count("month"))
        st.metric(label="Offboards (Month)", value=get_offboards_count("month"))
    
    with col3:
        st.metric(label="Completed Onboardings (Month)", value=get_completed_onboardings_count("month"))
        st.metric(label="Completed Onboardings (Semester)", value=get_completed_onboardings_count("semester"))


def display_graphs():
    st.subheader("Hiring and Onboarding Trends 📊")
    
    monthly_data = get_monthly_hires_data()
    
    if not monthly_data:
        st.warning("No data available for the graph.")
        return
    
    # Prepare data for plotting
    months = [item['_id'] for item in monthly_data]
    new_hires = [item.get('new_hires', 0) for item in monthly_data]
    completed = [item.get('completed', 0) for item in monthly_data]
    
    # Create a grouped bar chart
    fig = go.Figure(data=[
        go.Bar(name='New Hires', x=months, y=new_hires),
        go.Bar(name='Completed Onboardings', x=months, y=completed)
    ])
    
    # Customize the layout
    fig.update_layout(
        title='Monthly New Hires and Completed Onboardings',
        xaxis_title='Month',
        yaxis_title='Count',
        barmode='group'
    )
    
    # Display the chart
    st.plotly_chart(fig)

def display_training_setup_progress():
    st.subheader("Training and Setup Progress 🔄")
    
    employees = get_recent_hires_with_tasks()
    selected_employee = st.selectbox("Select Employee", 
                                     options=[f"{e['first_name']} {e['last_name']}" for e in employees],
                                     format_func=lambda x: x)
    
    if selected_employee:
        employee = next(e for e in employees if f"{e['first_name']} {e['last_name']}" == selected_employee)
        employee_id = str(employee['_id'])
        
        st.write(f"Started on: {employee['start_date'].strftime('%Y-%m-%d')}")
        
        employee_tasks = get_employee_tasks(employee_id).get('tasks', {})
        all_tasks = get_onboarding_tasks()
        
        total_tasks = 0
        completed_tasks = 0
        
        for day, tasks in all_tasks.items():
            with st.expander(day):
                for task in tasks:
                    task_status = employee_tasks.get(day, {}).get(task, False)
                    st.markdown(f"{'✅' if task_status else '❌'} {task}")
                    total_tasks += 1
                    if task_status:
                        completed_tasks += 1
        
        progress = completed_tasks / total_tasks if total_tasks > 0 else 0
        st.progress(progress)
        st.write(f"Overall progress: {completed_tasks}/{total_tasks} tasks completed")


# Define pages
home_page = st.Page(home, title="Home", icon="🏠")
onboarding_page = st.Page(onboarding, title="Onboarding", icon="🆕")
offboarding_page = st.Page(offboarding, title="Offboarding", icon="👋")
notes_page = st.Page(notes, title="Notes", icon="📝")
admin_page = st.Page(admin, title="Admin", icon="🔐")
logout_page = st.Page(logout, title="Log out", icon="🚪")

# Main app
if st.session_state.user_email and st.session_state.role:
    pages = {
        "Main": [home_page, onboarding_page, offboarding_page, notes_page],
        "Account": [logout_page]
    }
    
    # Only add the admin page for IT Managers
    if st.session_state.role == "IT Manager":
        pages["Admin"] = [admin_page]
    
    pg = st.navigation(pages)
else:
    pg = st.navigation([st.Page(login_signup)])

pg.run()