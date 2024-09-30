import streamlit as st
from src.database import get_employee_by_name, update_employee_access

def offboarding():
    st.title("🚪 Employee Offboarding Process")

    # Input fields for employee name
    col1, col2 = st.columns(2)
    with col1:
        first_name = st.text_input("First Name")
    with col2:
        last_name = st.text_input("Last Name")

    # Start Offboard button
    if st.button("Start Offboard"):
        if first_name and last_name:
            full_name = f"{first_name} {last_name}"
            employee = get_employee_by_name(full_name)
            
            if employee:
                st.subheader(f"Access Controls for {full_name}")
                
                # Display current access controls with checkboxes
                access_controls = employee.get('access_controls', [])
                updated_controls = []
                
                for control in access_controls:
                    if st.checkbox(control, value=True, key=f"access_{control}"):
                        updated_controls.append(control)
                
                # Update button
                if st.button("Update Access Controls"):
                    if update_employee_access(full_name, updated_controls):
                        st.success(f"Updated access controls for {full_name}")
                    else:
                        st.error("Failed to update access controls. Please try again.")
            else:
                st.error(f"Employee {full_name} not found in the database.")
        else:
            st.error("Please enter both first and last name.")

if __name__ == "__main__":
    offboarding()