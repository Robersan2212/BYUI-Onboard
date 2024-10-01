import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import sys

# Global variables
client = None
db = None
main_collection = None
user_collection = None
notes_collection = None

def initialize_database():
    global client, db, main_collection, user_collection, notes_collection
    
    try:
        mongodb_uri = st.secrets['MONGODB_URI']
        print(f"Attempting to connect with URI: {mongodb_uri.split('@')[1]}")
        
        # Create a new client and connect to the server
        client = MongoClient(mongodb_uri, server_api=ServerApi('1'))
        
        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")

        # Get the database and collections
        db = client['Staffing']
        main_collection = db['main_data']
        user_collection = db['users']
        notes_collection = db['notes']
        
        print(f"Connected to database: {db.name}")
        print(f"Using main collection: {main_collection.name}")
        print(f"Using user collection: {user_collection.name}")
        print(f"Using notes collection: {notes_collection.name}")
        
        return True

    except Exception as e:
        print(f"An error occurred while connecting to the database: {e}", file=sys.stderr)
        return False

def check_connection():
    if client is None or db is None:
        raise Exception("Database connection not established. Call initialize_database() first.")

# User-related functions

def add_user(email, hashed_password, role):
    check_connection()
    user = {
        "email": email,
        "password": hashed_password,
        "role": role
    }
    result = user_collection.insert_one(user)
    return result.acknowledged

def get_user_by_email(email):
    check_connection()
    return user_collection.find_one({"email": email})

def update_user_role(email, new_role):
    check_connection()
    result = user_collection.update_one(
        {"email": email},
        {"$set": {"role": new_role}}
    )
    return result.modified_count == 1

# Employee-related functions

def add_employee(name, email, i_number, phone_number, position, start_date, status="Not Started", progress=0):
    check_connection()
    start_date_str = start_date.strftime("%Y-%m-%d")
    
    employee = {
        "name": name,
        "email": email,
        "i_number": i_number,
        "phone_number": phone_number,
        "position": position,
        "start_date": start_date_str,
        "status": status,
        "progress": progress,
        "access_controls": []
    }
    result = main_collection.insert_one(employee)
    return result.acknowledged

def get_all_employees():
    check_connection()
    return list(main_collection.find())

def get_employee_by_name(name):
    check_connection()
    return main_collection.find_one({"name": name})

def get_total_new_hires():
    check_connection()
    return main_collection.count_documents({})

def get_total_offboards():
    check_connection()
    return main_collection.count_documents({"status": "Offboarded"})

def get_onboarding_this_month():
    check_connection()
    current_month = datetime.now().month
    current_year = datetime.now().year
    return main_collection.count_documents({
        "start_date": {"$regex": f"^{current_year}-{current_month:02d}"},
        "status": {"$ne": "Completed"}
    })

def get_completed_this_month():
    check_connection()
    current_month = datetime.now().month
    current_year = datetime.now().year
    return main_collection.count_documents({
        "start_date": {"$regex": f"^{current_year}-{current_month:02d}"},
        "status": "Completed"
    })

def get_onboarding_data():
    check_connection()
    pipeline = [
        {
            "$group": {
                "_id": {"$substr": ["$start_date", 0, 7]},
                "Completed": {"$sum": {"$cond": [{"$eq": ["$status", "Completed"]}, 1, 0]}},
                "In Progress": {"$sum": {"$cond": [{"$eq": ["$status", "In Progress"]}, 1, 0]}}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    return list(main_collection.aggregate(pipeline))

def update_employee_progress(name, progress, status):
    check_connection()
    result = main_collection.update_one(
        {"name": name},
        {"$set": {"progress": progress, "status": status}}
    )
    return result.modified_count == 1

def update_employee_access(name, access_controls):
    check_connection()
    result = main_collection.update_one(
        {"name": name},
        {"$set": {"access_controls": access_controls}}
    )
    return result.modified_count == 1

def delete_employee(name):
    check_connection()
    result = main_collection.delete_one({"name": name})
    return result.deleted_count == 1

# Note-related functions

def add_note(user, content):
    check_connection()
    note = {
        "user": user,
        "content": content,
        "date": datetime.now()
    }
    result = notes_collection.insert_one(note)
    return result.acknowledged

def get_notes_by_user(user):
    check_connection()
    return list(notes_collection.find({"user": user}).sort("date", -1))

def get_all_notes():
    check_connection()
    return list(notes_collection.find().sort("date", -1))

# Test connection and print database info
if __name__ == "__main__":
    if initialize_database():
        print(f"Total employees: {get_total_new_hires()}")
        print(f"Employees onboarding this month: {get_onboarding_this_month()}")
        print(f"Employees completed this month: {get_completed_this_month()}")
    else:
        print("Failed to initialize database connection.", file=sys.stderr)