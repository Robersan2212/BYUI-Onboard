import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from pages.onboarding import onboarding, training_days
from pages.offboarding import offboarding
from pages.notes import notes
from src.database import (
    initialize_database,
    get_all_employees, get_total_new_hires, get_total_offboards,
    get_onboarding_this_month, get_completed_this_month, get_onboarding_data
)

# Page configuration
st.set_page_config(page_title="IT Staffing Dashboard", layout="wide")

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
    .emoji-title {
        font-size: 40px;
        font-weight: bold;
    }
    .spacer {
        height: 50px;
    }
</style>
""", unsafe_allow_html=True)

def home():
    st.markdown("<p class='emoji-title'>🖥️ IT Staffing Dashboard</p>", unsafe_allow_html=True)

    # Metrics with emojis
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    metrics = [
        ("👥 Total New Hires", get_total_new_hires()),
        ("🆕 Onboarding This Month", get_onboarding_this_month()),
        ("✅ Completed This Month", get_completed_this_month()),
        ("⏰ Overdue Tasks", 0),  # Placeholder
        ("🚪 Total Offboards", get_total_offboards()),
        ("📅 Offboard This Month", 0)  # Placeholder
    ]
    
    for i, (label, value) in enumerate(metrics):
        with eval(f"col{i+1}"):
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Add spacing
    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

    # Onboarding Progress Chart
    st.header("📊 Onboarding Progress")
    onboarding_data = get_onboarding_data()
    if onboarding_data:
        df = pd.DataFrame(onboarding_data)
        df['Month'] = pd.to_datetime(df['_id'] + '-01')  # Add '-01' to make it a valid date
        df['Month'] = df['Month'].dt.strftime('%b %Y')
        df = df.melt('Month', var_name='Status', value_name='Count', value_vars=['Completed', 'In Progress'])

        chart = alt.Chart(df).mark_bar().encode(
            x='Month:O',
            y='Count:Q',
            color=alt.Color('Status:N', scale=alt.Scale(domain=['Completed', 'In Progress'], range=['#4CAF50', '#2196F3'])),
            column='Status:N'
        ).properties(width=300)

        st.altair_chart(chart)
    else:
        st.write("No onboarding data available yet.")

    # Training and Setup Progress
    st.header("🎓 Training and Setup Progress")
    employees = get_all_employees()
    if employees:
        if 'employee_progress' not in st.session_state:
            st.session_state.employee_progress = {emp['name']: emp.get('progress', 0) for emp in employees}

        selected_day = st.selectbox("Select Training Day", list(training_days.keys()))
    
        for employee in employees[:5]:  # Display for the 5 most recent hires
            st.subheader(f"{employee['name']} - {employee['position']}")
            progress = st.session_state.employee_progress[employee['name']]

            tasks = training_days[selected_day]
            total_tasks = sum(len(day_tasks) for day_tasks in training_days.values())
            completed_tasks = int(progress / 100 * total_tasks)
        
            for i, task in enumerate(tasks):
                task_index = sum(len(training_days[day]) for day in training_days if day < selected_day) + i
                if task_index < completed_tasks:
                    color = "#4CAF50"  # Completed (Green)
                elif task_index == completed_tasks:
                    color = "#2196F3"  # In Progress (Blue)
                else:
                    color = "#E0E0E0"  # Not Started (Light Gray)
            
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                    <div style="background-color: {color}; width: 20px; height: 20px; margin-right: 10px; border-radius: 3px;"></div>
                    <div>{task}</div>
                </div>
                """, unsafe_allow_html=True)
        
            st.markdown("<hr>", unsafe_allow_html=True)  # Add a separator between employees
    else:
        st.write("No employees to display in the Training and Setup Progress.")

def main():
    # Initialize the database connection
    if not initialize_database():
        st.error("Failed to connect to the database. Please check your connection and try again.")
        return

    # Define pages with emojis
    pages = {
        "🏠 Home": home,
        "🆕 Onboarding": onboarding,
        "🚪 Offboarding": offboarding,
        "📝 Notes": notes
    }

    # Sidebar navigation with emojis
    st.sidebar.title("Navigation")
    
    # Use session state to keep track of the selected page
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Home"

    for page_name in pages.keys():
        if st.sidebar.button(page_name, key=page_name):
            st.session_state.current_page = page_name

    # Display the selected page
    pages[st.session_state.current_page]()

if __name__ == "__main__":
    main()