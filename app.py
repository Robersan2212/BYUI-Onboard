import streamlit as st
import pandas as pd
import altair as alt  
from datetime import datetime
from src.database import (
    get_all_employees, get_total_new_hires, get_total_offboards,
    get_onboarding_this_month, get_completed_this_month, get_onboarding_data,
    add_employee, update_employee_progress, offboard_employee
)


# Custom CSS for styling
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    .stProgress {
        height: 20px;
    }
    .metric-card {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 10px;
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
    }
    .metric-label {
        font-size: 14px;
        color: #888;
    }
</style>
""", unsafe_allow_html=True)

def home():
    st.title("IT Staffing Dashboard")

    # Metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    metrics = [
        ("Total New Hires", get_total_new_hires()),
        ("Onboarding This Month", get_onboarding_this_month()),
        ("Completed This Month", get_completed_this_month()),
        ("Overdue Tasks", 0),  # Placeholder
        ("Total Offboards", get_total_offboards()),
        ("Offboard This Month", 0)  # Placeholder
    ]
    
    for i, (label, value) in enumerate(metrics):
        with eval(f"col{i+1}"):
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    # Onboarding Progress Chart
    st.header("Onboarding Progress")
    onboarding_data = get_onboarding_data()
    if onboarding_data:
        df = pd.DataFrame(onboarding_data)
        df['Month'] = pd.to_datetime(df['_id'], format='%m').dt.strftime('%b')
        df = df.melt('Month', var_name='Status', value_name='Count')
        
        chart = alt.Chart(df).mark_bar().encode(
            x='Month:O',
            y='Count:Q',
            color=alt.Color('Status:N', scale=alt.Scale(domain=['Completed', 'In Progress'], range=['#4CAF50', '#2196F3'])),
            column='Status:N'
        ).properties(width=300)
        
        st.altair_chart(chart)
    else:
        st.write("No onboarding data available yet.")

    # Recent New Hires
    st.header("Recent New Hires")
    employees = get_all_employees()
    if employees:
        recent_hires = employees[:5]  # Get the 5 most recent hires
        for hire in recent_hires:
            col1, col2, col3 = st.columns([2, 2, 4])
            col1.write(hire['name'])
            col2.write(hire['position'])
            col3.progress(int(hire['progress']) / 100)
    else:
        st.write("No recent hires to display.")

    # Training and Setup Progress
    st.header("Training and Setup Progress")
    if employees:
        stages = ["Paperwork", "IT Setup", "Orientation", "Department Training", "Project Assignment"]
        for employee in employees[:5]:  # Display for the 5 most recent hires
            st.subheader(f"{employee['name']} - {employee['position']}")
            cols = st.columns(len(stages))
            for i, stage in enumerate(stages):
                with cols[i]:
                    progress = int(employee['progress'])
                    if i < progress // 20:
                        color = "#4CAF50"  # Completed
                    elif i == progress // 20:
                        color = "#2196F3"  # In Progress
                    else:
                        color = "#E0E0E0"  # Not Started
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <div style="font-size: 12px;">{stage}</div>
                        <div style="background-color: {color}; height: 20px; border-radius: 10px;"></div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.write("No employees to display in the Training and Setup Progress.")

def notes():
    st.title("Notes")
    st.write("This is the Notes page.")
    # Add functionality for notes here

def offboarding():
    st.title("Offboarding")
    st.write("This is the Offboarding page.")
    # Add offboarding functionality here

def onboarding():
    st.title("Onboarding")
    st.write("This is the Onboarding page.")
    
    # Form to add a new employee
    with st.form("new_employee_form"):
        name = st.text_input("Name")
        position = st.text_input("Position")
        start_date = st.date_input("Start Date")
        submitted = st.form_submit_button("Start Onboarding")
        if submitted:
            add_employee(name, position, start_date)
            st.success(f"Started onboarding process for {name}!")

    # Form to update employee progress
    st.subheader("Update Employee Progress")
    employees = get_all_employees()
    if employees:
        employee_names = [emp['name'] for emp in employees if emp['progress'] < 100]
        if employee_names:
            with st.form("update_progress_form"):
                selected_employee = st.selectbox("Select Employee", employee_names)
                progress = st.slider("Progress", 0, 100, 0)
                update_submitted = st.form_submit_button("Update Progress")
                if update_submitted:
                    update_employee_progress(selected_employee, progress)
                    st.success(f"Updated progress for {selected_employee}!")
        else:
            st.write("No employees currently in the onboarding process.")
    else:
        st.write("No employees to update.")

# Define pages
home_page = st.Page(home, title="Home", icon="🏠")
notes_page = st.Page(notes, title="Notes", icon="📝")
offboarding_page = st.Page(offboarding, title="Offboarding", icon="👋")
onboarding_page = st.Page(onboarding, title="Onboarding", icon="🆕")

# Create navigation
pages = [home_page, notes_page, offboarding_page, onboarding_page]
pg = st.navigation(pages)

# Run the selected page
pg.run()
