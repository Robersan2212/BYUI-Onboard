import traceback
import streamlit as st
import bcrypt
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime, timedelta
from bson.objectid import ObjectId

# Use the MongoDB URI from Streamlit secrets
mongo_uri = st.secrets['MONGODB_URI']

# Create a new client and connect to the server
client = MongoClient(mongo_uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Get a reference to the database
db = client.employee_onboarding



def save_user_state(username, state):
    db.user_states.update_one(
        {"username": username},
        {"$set": state},
        upsert=True
    )

def get_user_state(username):
    return db.user_states.find_one({"username": username})

def get_all_trainers():
    return list(db.users.find({"role": "Trainer"}, {"email": 1, "created_at": 1}))

def delete_user(user_id):
    result = db.users.delete_one({"_id": ObjectId(user_id)})
    return result.deleted_count > 0

def create_signup_request(email, password, role):
    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    signup_request = {
        "email": email,
        "password": hashed_password,
        "role": role,
        "created_at": datetime.now(),
        "status": "pending"
    }
    result = db.signup_requests.insert_one(signup_request)
    return result.inserted_id

def get_pending_signup_requests():
    return list(db.signup_requests.find({"status": "pending"}))

def approve_signup_request(request_id):
    request = db.signup_requests.find_one({"_id": ObjectId(request_id)})
    if request:
        create_user(request['email'], request['password'], request['role'])
        db.signup_requests.update_one({"_id": ObjectId(request_id)}, {"$set": {"status": "approved"}})
        return True
    return False

def deny_signup_request(request_id):
    result = db.signup_requests.update_one({"_id": ObjectId(request_id)}, {"$set": {"status": "denied"}})
    return result.modified_count > 0

# New functions for user authentication
def create_user(email, hashed_password, role):
    user = {
        "email": email,
        "password": hashed_password,
        "role": role,
        "created_at": datetime.now()
    }
    result = db.users.insert_one(user)
    return result.inserted_id


def verify_user(email, password):
    user = db.users.find_one({"email": email})
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return user
    return None

def get_user_role(email):
    user = db.users.find_one({"email": email})
    return user['role'] if user else None

def add_new_hire(first_name, last_name, email, i_number, date_of_birth, start_date):
    new_hire = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "i_number": i_number,
        "date_of_birth": datetime.combine(date_of_birth, datetime.min.time()),  # Convert to datetime
        "start_date": datetime.combine(start_date, datetime.min.time()),
    }
    result = db.employees.insert_one(new_hire)
    print(f"Debug: New hire added with ID: {result.inserted_id}")
    return result.inserted_id

def get_access_control_task():
    return{
        "Hired in Workday": False,
        "Canvas": False,
            "Role Manager": False,
            "TD": False,
            "TD Dashboard": False,
            "Gensys": False,
            "Gensys Queues": False,
            "OL Account": False,
            "Zoom Lockout": {"status":False, "url":"https://byui.zoom.us/account/user#/"},
            "Zoho": {"status":False, "url": "https://directory.zoho.com/directory/byuidaho/adminhome#/orgdomains"},
            "Duo": False,
            "KB Catalog": False,
            "Teams": False,
            "Proxy Card": False,
            "Proxy Card Access": {"status":False, "url": "https://web.byui.edu/AccessControl/home"},
            "Onboarding with Governance": False,
            "Name Tags": False

    }


def update_onboarding_tasks(employee_id, tasks):
    db.employees.update_one(
        {"_id": ObjectId(employee_id)},
        {"$set": {"onboarding_tasks": tasks}}
    )


def get_onboarding_tasks():
    return {
        "Day 1": [
            "FERPA Training",
            "Color Code Personality"
        ],
        "Day 2": [
            "TeamDynamix",
            "FERPA Restrictions",
            "Meet with KM Team"
        ],
        "Day 3": [
            "Call Rubric w/ Auditor",
            "ZOHO quiz",
            "Day 3 Call Shadowing"
        ],
        "Day 4": [
            "Chat Rubric w/ Auditor",
            "Day 4 Chat Shadowing",
            "Ticket Definitions Quiz"
        ],
        "Day 5": [
            "Ticket Rubric w/ Auditor",
            "Meet with Ticketing Team",
            "Password Reset Scenario (Call)",
            "Password Reset Scenario (Chat)",
            "DUO Scenario",
            "Day 5 Shadowing"
        ],
        "Day 6": [
            "Classroom Emergency Ticket",
            "Supervised Chats",
            "Zoom/Kaltura Scenario"
        ],
        "Day 7": [
            "Common Troubleshooting",
            "Supervised Chats",
            "Supervised Calls"
        ],
        "Day 8": [
            "Account Issues",
            "Adobe Creative Cloud",
            "Supervised Phone Calls",
            "Supervised Chats"
        ],
        "Day 9": [
            "Pathway Students",
            "Day 9 Shadowing",
            "Supervised Calls",
            "Supervised Chats"
        ],
        "Day 10": [
            "Daily 4",
            "Final Exam",
            "Exit One-on-One"
        ]
    }

def update_task_status(employee_id, day, task, status):
    db.employees.update_one(
        {"_id": ObjectId(employee_id)},
        {"$set": {f"tasks.{day}.{task}": status}}
    )
    print(f"Debug: Updated task status for employee {employee_id}, {day}, {task}: {status}")

def get_employee_tasks(employee_id):
    try:
        employee = db.employees.find_one({"_id": ObjectId(employee_id)})
        if employee:
            print(f"Debug: Found employee: {employee}")
            return employee
        else:
            print(f"Debug: No employee found with ID: {employee_id}")
            return None
    except Exception as e:
        print(f"Debug: Error in get_employee_tasks: {str(e)}")
        return None

def get_recent_hires_with_tasks(limit=10):
    return list(db.employees.find(
        {"status": {"$ne": "completed"}},
        {"first_name": 1, "last_name": 1, "start_date": 1, "tasks": 1}
    ).sort("start_date", -1).limit(limit))

@st.cache_data(ttl=0)
def get_new_hires_count(period):
    print(f"Getting new hires count for period: {period}")
    end_date = datetime.now()
    if period == "semester":
        start_date = end_date - timedelta(days=180)
    elif period == "month":
        start_date = end_date - timedelta(days=30)
    else:
        raise ValueError("Invalid period. Use 'semester' or 'month'.")
    
    count = db.employees.count_documents({
        "start_date": {"$gte": start_date, "$lte": end_date},
        "status": {"$ne": "completed"}
    })
    print(f"New hires count for {period}: {count}")
    return count

def get_recent_hires(limit=5):
    return list(db.employees.find(
        {"status": {"$ne": "completed"}},
        {"first_name": 1, "last_name": 1, "start_date": 1}
    ).sort("start_date", -1).limit(limit))

def get_monthly_hires_data():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    pipeline = [
        {
            "$match": {
                "$or": [
                    {"start_date": {"$gte": start_date, "$lte": end_date}},
                    {"completion_date": {"$gte": start_date, "$lte": end_date}}
                ]
            }
        },
        {
            "$project": {
                "year_month": {
                    "$dateToString": {
                        "format": "%Y-%m",
                        "date": {
                            "$cond": [
                                {"$gte": ["$start_date", start_date]},
                                "$start_date",
                                "$completion_date"
                            ]
                        }
                    }
                },
                "is_new_hire": {"$cond": [{"$gte": ["$start_date", start_date]}, 1, 0]},
                "is_completed": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
            }
        },
        {
            "$group": {
                "_id": "$year_month",
                "new_hires": {"$sum": "$is_new_hire"},
                "completed": {"$sum": "$is_completed"}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    result = list(db.employees.aggregate(pipeline))
    
    # Ensure all months have both 'new_hires' and 'completed' keys
    all_months = set(item['_id'] for item in result)
    for month in all_months:
        if not any(item['_id'] == month for item in result):
            result.append({'_id': month, 'new_hires': 0, 'completed': 0})
    
    return sorted(result, key=lambda x: x['_id'])


def search_employee(first_name, last_name):
    print(f"Searching for employee: {first_name} {last_name}")
    query = {
        "first_name": {"$regex": f"^{first_name}$", "$options": "i"},
        "last_name": {"$regex": f"^{last_name}$", "$options": "i"}
    }
    print(f"Query: {query}")
    result = db.employees.find_one(query)
    if result:
        print(f"Employee found: {result}")
    else:
        print("No employee found")
        # Print all employees to see what's in the database
        all_employees = list(db.employees.find())
        print(f"All employees in database: {all_employees}")
    return result

def start_offboarding(employee_id):
    # This function could be used to update the employee's status to "offboarding"
    # or to create a new document in an "offboarding" collection
    db.employees.update_one({"_id": employee_id}, {"$set": {"status": "offboarding"}})

def finish_offboarding(employee_id):
    # This function removes the employee from the database
    db.employees.delete_one({"_id": employee_id})

def get_offboarding_tasks():
    return {
        "Hired in Workday": False,
        "Canvas": False,
            "Role Manager": False,
            "TD": False,
            "TD Dashboard": False,
            "Gensys": False,
            "Gensys Queues": False,
            "OL Account": False,
            "Zoom Lockout": {"status":False, "url":"https://byui.zoom.us/account/user#/"},
            "Zoho": {"status":False, "url": "https://directory.zoho.com/directory/byuidaho/adminhome#/orgdomains"},
            "Duo": False,
            "KB Catalog": False,
            "Teams": False,
            "Proxy Card": False,
            "Proxy Card Access": {"status":False, "url": "https://web.byui.edu/AccessControl/home"},
            "Onboarding with Governance": False,
            "Name Tags": False
    }

def create_note(user, title, topic, content):
    note = {
        "user": user,
        "title": title,
        "topic": topic,
        "content": content,
        "created_at": datetime.now()
    }
    result = db.notes.insert_one(note)
    return result.inserted_id


def remove_hire(employee_id):
    try:
        object_id = ObjectId(employee_id)
        result = db.employees.delete_one({"_id": object_id})
        print(f"Remove hire result: {result.deleted_count}")
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error in remove_hire: {str(e)}")
        return False

def get_all_notes():
    return list(db.notes.find().sort("created_at", -1))

def delete_note(note_id):
    result = db.notes.delete_one({"_id": ObjectId(note_id)})
    if result.deleted_count == 0:
        raise Exception("No note found with the given ID")
    return True

def update_note(note_id, title, topic, content):
    db.notes.update_one(
        {"_id": ObjectId(note_id)},
        {
            "$set": {
                "title": title,
                "topic": topic,
                "content": content,
                "updated_at": datetime.now()
            }
        }
    )

# Additional functions for other metrics
@st.cache_data(ttl=0)
def get_offboards_count(period):
    print(f"Getting offboards count for period: {period}")
    end_date = datetime.now()
    if period == "semester":
        start_date = end_date - timedelta(days=180)
    elif period == "month":
        start_date = end_date - timedelta(days=30)
    else:
        raise ValueError("Invalid period. Use 'semester' or 'month'.")
    
    count = db.offboards.count_documents({"date": {"$gte": start_date, "$lte": end_date}})
    print(f"Offboards count for {period}: {count}")
    return count

def update_offboard_count(offboard_date):
    try:
        db.offboards.insert_one({"date": offboard_date})
        result = db.summary.update_one(
            {"_id": "offboard_summary"},
            {"$inc": {"total_offboards": 1, f"offboards_{offboard_date.strftime('%Y-%m')}": 1}},
            upsert=True
        )
        print(f"Update offboard count result: {result.modified_count}")
        return True
    except Exception as e:
        print(f"Error in update_offboard_count: {str(e)}")
        return False

@st.cache_data(ttl=0)
def get_completed_onboardings_count(period):
    print(f"Getting completed onboardings count for period: {period}")
    end_date = datetime.now()
    if period == "semester":
        start_date = end_date - timedelta(days=180)
    elif period == "month":
        start_date = end_date - timedelta(days=30)
    else:
        raise ValueError("Invalid period. Use 'semester' or 'month'.")
    
    count = db.employees.count_documents({
        "status": "completed",
        "completion_date": {"$gte": start_date, "$lte": end_date}
    })
    print(f"Completed onboardings count for {period}: {count}")
    return count

def mark_employee_completed(employee_id):
    result = db.employees.update_one(
        {"_id": ObjectId(employee_id)},
        {
            "$set": {
                "status": "completed",
                "completion_date": datetime.now()
            }
        }
    )
    return result.modified_count > 0


def reset_offboard_table():
    try:
        result = db.offboards.delete_many({})
        deleted_count = result.deleted_count
        print(f"Deleted {deleted_count} documents from the offboards collection")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def get_overdue_tasks_count():
    # Placeholder function - implement actual logic when tasks are tracked
    return 0