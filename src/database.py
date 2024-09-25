import streamlit as st
from pymongo import MongoClient
import pandas as pd
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus

username = st.secrets['USERNAME']
db_password = st.secrets['PASSWORD']
db = st.secrets['DATA_BASE']
collection = st.secrets['COLLECTION']
uri_base = st.secrets['MONGODB_URI_BASE']

# Construct the full URI with escaped username and password
mongodb_uri = uri_base.format(
    username=quote_plus(username),
    password=quote_plus(db_password)
)


# Create a new client and connect to the server
client = MongoClient(mongodb_uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
