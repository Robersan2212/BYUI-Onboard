import streamlit as st
from datetime import datetime, timedelta
import bcrypt
from functools import wraps
from src.database import initialize_database, add_user, get_user_by_email, update_user_role

# Initialize the database connection
if not initialize_database():
    st.error("Failed to connect to the database. Please check your connection and try again.")

# Define roles and permissions
ROLES = {
    'It_manager': ['view_all', 'admin', 'edit_all', 'edit_training'],
    'Trainer': ['view_all', 'edit_training'],
}

IDLE_TIMEOUT = timedelta(minutes=30)
ABSOLUTE_TIMEOUT = timedelta(hours=8)

def init_session_state():
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'login_time' not in st.session_state:
        st.session_state.login_time = None
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = None

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def login(email, password):
    user = get_user_by_email(email)
    if user and check_password(password, user['password']):
        st.session_state.user = user
        st.session_state.login_time = datetime.now()
        st.session_state.last_activity = datetime.now()
        return True
    return False

def signup(email, password, role='Trainer'):
    if get_user_by_email(email):
        return False, "Email already exists"
    
    hashed_password = hash_password(password)
    success = add_user(email, hashed_password, role)
    if success:
        return True, "User created successfully"
    return False, "Failed to create user"

def check_session():
    if st.session_state.user and st.session_state.login_time:
        now = datetime.now()
        if now - st.session_state.login_time > ABSOLUTE_TIMEOUT:
            logout()
            return False
        if now - st.session_state.last_activity > IDLE_TIMEOUT:
            logout()
            return False
        st.session_state.last_activity = now
        return True
    return False

def logout():
    st.session_state.user = None
    st.session_state.login_time = None
    st.session_state.last_activity = None

def check_permission(permission):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not check_session():
                st.error("Please log in first.")
                return
            user = st.session_state.user
            role = user['role']
            if role == "It_manager" or (role == "Trainer" and permission != "admin"):
                return func(*args, **kwargs)
            else:
                st.error("You don't have permission to access this page.")
        return wrapper
    return decorator

def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if check_session():
            return func(*args, **kwargs)
        else:
            st.error("Please log in to access this page.")
    return wrapper

def auth_page():
    st.title("Authentication")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.header("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            if login(email, password):
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid email or password")

    with tab2:
        st.header("Sign Up")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        role = st.selectbox("Role", options=["Trainer", "It_manager"])
        
        if st.button("Sign Up"):
            if new_password != confirm_password:
                st.error("Passwords do not match")
            else:
                success, message = signup(new_email, new_password, role)
                if success:
                    st.success(message)
                    st.info("Please log in with your new account")
                else:
                    st.error(message)

def show_user_info():
    if st.session_state.user:
        st.sidebar.write(f"Logged in as: {st.session_state.user['email']}")
        st.sidebar.write(f"Role: {st.session_state.user['role']}")
        if st.sidebar.button("Logout"):
            logout()
            st.rerun()