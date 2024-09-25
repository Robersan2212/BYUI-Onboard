import streamlit as st
import pandas as pd
import altair as alt  
from datetime import datetime

# Page configuration - This must be the first Streamlit command in the page///
st.set_page_config(page_title="Onboard", layout="wide")

def waffle_menu():
    menu_items = [
        {"name": "Onboarding", "icon": "🆕"},
        {"name": "Offboarding", "icon": "🚪"},
        {"name": "Notes", "icon": "📝"}
    ]
    
    st.markdown("""
    <style>
    .waffle-menu {
        display: inline-block;
        position: relative;
    }
    .waffle-button {
        background-color: #f0f2f6;
        border: none;
        padding: 10px;
        font-size: 20px;
        cursor: pointer;
    }
    .waffle-content {
        display: none;
        position: absolute;
        background-color: #f9f9f9;
        min-width: 160px;
        box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
        z-index: 1;
        opacity: 0;
        transform: translateY(-20px);
        transition: opacity 0.3s, transform 0.3s;
    }
    .waffle-content.show {
        opacity: 1;
        transform: translateY(0);
    }
    .waffle-content a {
        color: black;
        padding: 12px 16px;
        text-decoration: none;
        display: block;
        transition: background-color 0.2s;
    }
    .waffle-content a:hover {
        background-color: #f1f1f1;
    }
    </style>
    """, unsafe_allow_html=True)

    menu_html = """
    <div class="waffle-menu">
        <button class="waffle-button" onclick="toggleWaffleMenu()"></button>
        <div id="waffleMenu" class="waffle-content">
    """
    
    for item in menu_items:
        menu_html += f'<a href="#">{item["icon"]} {item["name"]}</a>'
    
    menu_html += """
        </div>
    </div>
    <script>
    function toggleWaffleMenu() {
        var menu = document.getElementById("waffleMenu");
        menu.style.display = menu.style.display === "block" ? "none" : "block";
        setTimeout(() => {
            menu.classList.toggle("show");
        }, 10);
    }
    </script>
    """
    
    st.markdown(menu_html, unsafe_allow_html=True)
    pass


# Add the waffle menu
waffle_menu()


# Initialize session state
if 'employees' not in st.session_state:
    st.session_state.employees = pd.DataFrame(columns=['Name', 'Position', 'Status', 'Start Date', 'Progress'])
    st.session_state.employees['Start Date'] = pd.to_datetime(st.session_state.employees['Start Date'])

if 'total_new_hires' not in st.session_state:
    st.session_state.total_new_hires = 0  # Example data

if 'total_offboards' not in st.session_state:
    st.session_state.total_offboards = 0  # Example data

# Main dashboard
st.title("Onboarding/Offboarding Dashboard")

# Helper function to create a metric with an icon
def metric_with_icon(icon, label, value):
    st.markdown(f'<div style="display: flex; align-items: center;">'
                f'<div style="font-size: 24px; margin-right: 10px;">{icon}</div>'
                f'<div>'
                f'<div style="font-size: 14px; color: #888;">{label}</div>'
                f'<div style="font-size: 24px; font-weight: bold;">{value}</div>'
                f'</div></div>', unsafe_allow_html=True)

# Create columns for metrics
col1, col2, col3, col4, col5, col6 = st.columns(6)

# Display metrics
with col1:
    metric_with_icon("👥", "Total New Hires", st.session_state.total_new_hires)

with col2:
    current_month = datetime.now().month
    onboarding_this_month = len(st.session_state.employees[
        (st.session_state.employees['Start Date'].dt.month == current_month) & 
        (st.session_state.employees['Status'] != 'Completed')
    ])
    metric_with_icon("🆕", "Onboarding This Month", onboarding_this_month)

with col3:
    completed_this_month = len(st.session_state.employees[
        (st.session_state.employees['Start Date'].dt.month == current_month) & 
        (st.session_state.employees['Status'] == 'Completed')
    ])
    metric_with_icon("✅", "Completed This Month", completed_this_month)

with col4:
    overdue_tasks = 0  # Example data
    metric_with_icon("⏰", "Overdue Tasks", overdue_tasks)

with col5:
    metric_with_icon("🚪", "Total Offboards", st.session_state.total_offboards)

with col6:
    offboard_this_month = 0 # Example data
    metric_with_icon("📅", "Offboard This Month", offboard_this_month)




# Onboarding progress chart///
st.header("Onboarding Progress")
# DataFrame for onboarding chart
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May']
onboarding_data = pd.DataFrame({
    'Month': months,
    'Completed': [len(st.session_state.employees[(st.session_state.employees['Status'] == 'Completed') & (pd.to_datetime(st.session_state.employees['Start Date']).dt.month == i+1)]) for i in range(5)],
    'In Progress': [len(st.session_state.employees[(st.session_state.employees['Status'] == 'In Progress') & (pd.to_datetime(st.session_state.employees['Start Date']).dt.month == i+1)]) for i in range(5)]
})

chart = alt.Chart(onboarding_data.melt('Month', var_name='Status', value_name='Count')).mark_bar().encode(
    x='Month:O',
    y='Count:Q',
    color=alt.Color('Status:N', scale=alt.Scale(domain=['Completed', 'In Progress'], range=['#4CAF50', '#2196F3'])),
    column='Status:N'
).properties(
    width=300
)

st.altair_chart(chart)

# Recent new hires header
st.subheader("Recent New Hires")

# Sort employees by Start Date (most recent first) and take the top 5
recent_hires = st.session_state.employees.sort_values('Start Date', ascending=False).head(5)

for _, hire in recent_hires.iterrows():
    col1, col2, col3 = st.columns([2, 2, 4])
    with col1:
        st.write(hire['Name'])
    with col2:
        st.write(hire['Position'])
    with col3:
        progress = int(hire['Progress']) if pd.notnull(hire['Progress']) else 0
        st.progress(progress / 100)

# Display full employee table
st.dataframe(st.session_state.employees)

def create_progress_bar(status):
    colors = {
        "Completed": "#4CAF50",  # Green
        "In Progress": "#2196F3",  # Blue
        "Not Started": "#E0E0E0"  # Light Gray
    }
    return f'<span style="background-color: {colors[status]}; color: white; padding: 5px 10px; border-radius: 15px; margin-right: 5px;">{status}</span>'

def onboarding_progress():
    st.title("Training and Setup Progress")

    tasks = {
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

    employees = [
        {"name": "Employee1", "department": "Analyst"},
        {"name": "Employee2", "department": "Analyst"},
        {"name": "Employee3", "department": "Analyst"}
    ]

    tabs = st.tabs(list(tasks.keys()))

    for i, (day, day_tasks) in enumerate(tasks.items()):
        with tabs[i]:
            st.write(f"**{day}**")
            for employee in employees:
                st.write(f"{employee['name']} - {employee['department']}")
                for task in day_tasks:
                    status = "Completed" if i < 3 else ("In Progress" if i == 3 else "Not Started")
                    st.markdown(create_progress_bar(status) + f" {task}", unsafe_allow_html=True)
                st.write("")  # Add some space between employees



# Add the new onboarding progress component
onboarding_progress()
st.markdown("---")
