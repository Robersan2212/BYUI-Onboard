import streamlit as st
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import sys

# Global variables
client = None
db = None
main_collection = None

def initialize_database():
    global client, db, main_collection
    
    try:
        mongodb_uri = st.secrets['MONGODB_URI']
        print(f"Attempting to connect with URI: {mongodb_uri.split('@')[1]}")
        
        # Create a new client and connect to the server
        client = MongoClient(mongodb_uri, server_api=ServerApi('1'))
        
        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")

        # Get the database and collection
        db = client['Staffing']
        main_collection = db['main_data']
        
        print(f"Connected to database: {db.name}")
        print(f"Using collection: {main_collection.name}")
        
        return True

    except Exception as e:
        print(f"An error occurred while connecting to the database: {e}", file=sys.stderr)
        return False

# Initialize the database connection
initialize_database()

def add_employee(name, email, i_number, phone_number, position, start_date, status="Not Started", progress=0):
    global main_collection
    if main_collection is None:
        raise Exception("Database connection not established")
    
    # Convert start_date to string format
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
        "access_controls": []  # Initialize with empty list
    }
    main_collection.insert_one(employee)

def get_all_employees():
    global main_collection
    if main_collection is None:
        raise Exception("Database connection not established")
    return list(main_collection.find())

def get_employee_by_name(name):
    global main_collection
    if main_collection is None:
        raise Exception("Database connection not established")
    return main_collection.find_one({"name": name})

def get_total_new_hires():
    global main_collection
    if main_collection is None:
        raise Exception("Database connection not established")
    return main_collection.count_documents({})

def get_total_offboards():
    global main_collection
    if main_collection is None:
        raise Exception("Database connection not established")
    return main_collection.count_documents({"status": "Offboarded"})

def get_onboarding_this_month():
    global main_collection
    if main_collection is None:
        raise Exception("Database connection not established")
    current_month = datetime.now().month
    return main_collection.count_documents({
        "start_date": {"$regex": f"^{datetime.now().year}-{current_month:02d}"},
        "status": {"$ne": "Completed"}
    })

def get_completed_this_month():
    global main_collection
    if main_collection is None:
        raise Exception("Database connection not established")
    current_month = datetime.now().month
    return main_collection.count_documents({
        "start_date": {"$regex": f"^{datetime.now().year}-{current_month:02d}"},
        "status": "Completed"
    })

def get_onboarding_data():
    global main_collection
    if main_collection is None:
        raise Exception("Database connection not established")
    pipeline = [
        {
            "$group": {
                "_id": {
                    "$substr": [
                        "$start_date",
                        0,
                        7
                    ]
                },
                "Completed": {
                    "$sum": {
                        "$cond": [
                            {
                                "$eq": ["$status", "Completed"]
                            },
                            1,
                            0
                        ]
                    }
                },
                "In Progress": {
                    "$sum": {
                        "$cond": [
                            {
                                "$eq": ["$status", "In Progress"]
                            },
                            1,
                            0
                        ]
                    }
                }
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]
    return list(main_collection.aggregate(pipeline))

def update_employee_progress(name, progress, status):
    global main_collection
    if main_collection is None:
        raise Exception("Database connection not established")
    result = main_collection.update_one(
        {"name": name},
        {"$set": {"progress": progress, "status": status}}
    )
    return result.modified_count == 1

def update_employee_access(name, access_controls):
    global main_collection
    if main_collection is None:
        raise Exception("Database connection not established")
    result = main_collection.update_one(
        {"name": name},
        {"$set": {"access_controls": access_controls}}
    )
    return result.modified_count == 1

def delete_employee(name):
    global main_collection
    if main_collection is None:
        raise Exception("Database connection not established")
    
    result = main_collection.delete_one({"name": name})
    return result.deleted_count == 1

def add_note(user, content):
    global db
    if db is None:
        raise Exception("Database connection not established")
    notes_collection = db['notes']
    note = {
        "user": user,
        "content": content,
        "date": datetime.now()
    }
    notes_collection.insert_one(note)

def get_notes_by_user(user):
    global db
    if db is None:
        raise Exception("Database connection not established")
    notes_collection = db['notes']
    return list(notes_collection.find({"user": user}).sort("date", -1))

def get_all_notes():
    global db
    if db is None:
        raise Exception("Database connection not established")
    notes_collection = db['notes']
    return list(notes_collection.find().sort("date", -1))

# Test connection and print database info
if __name__ == "__main__":
    if initialize_database():
        print(f"Total employees: {get_total_new_hires()}")
        print(f"Employees onboarding this month: {get_onboarding_this_month()}")
        print(f"Employees completed this month: {get_completed_this_month()}")
    else:
        print("Failed to initialize database connection.", file=sys.stderr)