import streamlit as st
from src.auth.auth import require_auth, check_permission
from src.database import get_all_employees, update_user_role, get_user_by_email

@require_auth
@check_permission('admin')
def admin_page():
    st.title("👑 Admin Page")

    st.header("User Management")

    # Get all users (this is a simplified version, you might want to add pagination for large numbers of users)
    users = [user for user in get_all_employees() if 'role' in user]

    if users:
        for user in users:
            st.subheader(f"User: {user['email']}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"Current role: {user['role']}")
            with col2:
                new_role = st.selectbox("New role", ["Trainer", "It_manager"], key=f"role_{user['email']}")
            with col3:
                if st.button("Update Role", key=f"update_{user['email']}"):
                    if update_user_role(user['email'], new_role):
                        st.success(f"Updated role for {user['email']} to {new_role}")
                    else:
                        st.error(f"Failed to update role for {user['email']}")

    else:
        st.write("No users found.")

    st.header("System Statistics")
    
    # You can add more admin functionalities here, such as system statistics
    total_employees = len(get_all_employees())
    st.metric("Total Employees", total_employees)

    # Add more metrics or functionalities as needed

if __name__ == "__main__":
    admin_page()