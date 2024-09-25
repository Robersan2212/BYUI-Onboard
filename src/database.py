import streamlit as st
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

mongodb_uri = st.secrets['MONGODB_URI']

# Create a new client and connect to the server
client = MongoClient(mongodb_uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
