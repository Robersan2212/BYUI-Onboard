import streamlit as st
import datetime
from src.auth.auth import require_auth, check_permission
from src.database import add_employee, get_all_employees, update_employee_progress

# Define the training days and tasks
training_days = {
    "Day 1": ["FERPA Training", "Color Code Personality"],
    "Day 2": ["TeamDynamix", "FERPA Restrictions", "Meet with KM Team"],
    "Day 3": ["Call Rubric w/ Auditor", "ZOHO quiz", "Day 3 Call Shadowing"],
    "Day 4": ["Chat Rubric w/ Auditor", "Day 4 Chat Shadowing", "Ticket Definitions Quiz"],
    "Day 5": ["Ticket Rubric w/ Auditor", "Meet with Ticketing Team", "Password Reset Scenario (Call)", "Password Reset Scenario (Chat)", "Day 5 Shadowing"],
    "Day 6": ["Classroom Emergency Ticket", "DUO Scenario", "Zoom/Kaltura Scenario"],
    "Day 7": ["Common Troubleshooting", "Supervised Chats"],
    "Day 8": ["Account Issues", "Adobe Creative Cloud", "Supervised Phone Calls", "Supervised Chats"],
    "Day 9": ["Pathway Students", "Day 9 Shadowing", "Supervised Calls", "Supervised Chats"],
    "Day 10": ["Daily 4", "Final Exam", "Exit One-on-One"]
}


def onboarding():
    st.title("🆕 New Hire Onboarding")

    # New employee form
    with st.form("onboarding_form"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            email = st.text_input("Email")
        with col2:
            i_number = st.text_input("I-Number")
            phone_number = st.text_input("Phone Number")
            start_date = st.date_input("Starting Date", min_value=datetime.date.today())
        
        position = st.text_input("Position")
        
        # New Access Control section
        st.subheader("Access Control")
        access_controls = [
            "KB Catalog",
            "Teams",
            "Proxy Card",
            "Proxy Card Access",
            "Onboarding with Governance",
            "Name Tags"
        ]
        selected_controls = []
        for control in access_controls:
            if st.checkbox(control, key=f"access_{control}"):
                selected_controls.append(control)
        
        submitted = st.form_submit_button("Start Onboarding")
        
        if submitted:
            if first_name and last_name and email and i_number and phone_number and position:
                full_name = f"{first_name} {last_name}"
                if add_employee(full_name, email, i_number, phone_number, position, start_date, status="In Progress", progress=0):
                    st.success(f"Started onboarding process for {full_name}!")
                    st.rerun()
                else:
                    st.error("Failed to add employee. Please try again.")
            else:
                st.error("Please fill in all fields.")

    # Update employee progress
    st.header("Update Employee Progress")
    employees = get_all_employees()
    if employees:
        selected_employee = st.selectbox("Select Employee", [emp['name'] for emp in employees])
        selected_day = st.selectbox("Select Training Day", list(training_days.keys()))
        
        employee = next((emp for emp in employees if emp['name'] == selected_employee), None)
        if employee:
            if 'employee_progress' not in st.session_state:
                st.session_state.employee_progress = {}
            
            # Initialize progress for new employees
            if selected_employee not in st.session_state.employee_progress:
                st.session_state.employee_progress[selected_employee] = employee.get('progress', 0)

            current_progress = st.session_state.employee_progress[selected_employee]
            tasks = training_days[selected_day]
            total_tasks = sum(len(day_tasks) for day_tasks in training_days.values())
            
            st.write(f"Current overall progress: {current_progress}%")
            
            completed_tasks = 0
            for task in tasks:
                task_index = sum(len(training_days[day]) for day in training_days if day < selected_day) + tasks.index(task)
                is_completed = task_index < (current_progress / 100 * total_tasks)
                completed = st.checkbox(task, value=is_completed, key=f"{selected_employee}_{task}")
                if completed:
                    completed_tasks += 1

            new_progress = int((sum(len(training_days[day]) for day in training_days if day < selected_day) + completed_tasks) / total_tasks * 100)
            
            if new_progress != current_progress:
                st.session_state.employee_progress[selected_employee] = new_progress
                status = "In Progress" if new_progress < 100 else "Completed"
                if update_employee_progress(selected_employee, new_progress, status):
                    st.success(f"Updated progress for {selected_employee}!")
                else:
                    st.error("Failed to update employee progress. Please try again.")
        else:
            st.error("Selected employee not found.")
    else:
        st.write("No employees in the database to update.")

if __name__ == "__main__":
    onboarding()