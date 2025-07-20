import pandas as pd
from datetime import date
import streamlit as st
import json

# Function to append new data to JSON file
def write_json(new_data, filename='data.json'):
    with open(filename, 'r+') as file:
        file_data = json.load(file)

        file_data["configurations"].append(new_data)
        file.seek(0)
        json.dump(file_data, file, indent=4)

@st.dialog("Product added")
def product_added():
    st.write(f"Product added")
    
# -------------------------------------------------------------------
# READ FROM JSON
# -------------------------------------------------------------------
filename='data.json'

with open(filename, 'r+') as file:
    # Load existing data into a dictionary
    file_data = json.load(file)

configurations = file_data["configurations"]
products = []
mins = []
maxs = []

for product in configurations:
    products.append(product["keywords"])
    mins.append(product["min"])
    maxs.append(product["max"])

# -------------------------------------------------------------------
# PARAMETERS CONFIG
# -------------------------------------------------------------------
st.title(f"Search Data")

bot_token_input = st.text_input("Telegram bot token")
if not bot_token_input:
    bot_token_input = file_data["telegram_token"]

telegram_chat_input = st.text_input("Telegram chat id")
if not telegram_chat_input:
    telegram_chat_input = file_data["telegram_chat_id"]

time = st.number_input("Time between searches in minutes", 0, 2880, "min", 1)
if not time:
    time = file_data["time"]

st.write(f"Actual telegram bot token: {bot_token_input}")
st.write(f"Actual telegram chat id: {telegram_chat_input}")
st.write(f"Actual time between searches: {time}")
button = st.button("Update")

if button:
    if bot_token_input:
        file_data["telegram_token"] = bot_token_input
    if telegram_chat_input:
        file_data["telegram_chat_id"] = telegram_chat_input
    if time > 0:
        file_data["time"] = time
    with open('data.json','w') as f:
        json.dump(file_data,f,indent=2)

# -------------------------------------------------------------------
# FORM FOR ADDING PRODUCTS
# -------------------------------------------------------------------
st.title(f"Form for adding products")
with st.form("my_form"):
    st.write("Inside the form")
    product_name = st.text_input("Product to search")
    min = st.number_input("Min price", 0, 16777216, "min", 1)
    max = st.number_input("Max price", 0, 16777216, "min", 1)

    submitted = st.form_submit_button("Submit")
    if submitted:
        if max >= min:
            if product_name:
                product_dict = {
                    "keywords": product_name,
                    "min": min,
                    "max": max
                }
                write_json(product_dict)
                product_added()
                st.rerun()
            else:
                st.write(f"You need to enter a product name")
        else:
            st.write("Maximum price cant be over the minimum price")

# -------------------------------------------------------------------
# LIST OF ACTUAL PRODUCTS
# -------------------------------------------------------------------
st.title("Actual products")

for i, config in enumerate(configurations):
        with st.container(border=True):
            st.markdown(f"**{config['keywords']}**")
            st.markdown(f"Min price: {config['min']}")
            st.markdown(f"Max price: {config['max']}")
            delete_button = st.button("❌ Eliminar", key=f"delete_{i}")
            if delete_button:
                configurations.pop(i)
                file_data["configurations"] = configurations
                with open('data.json','w') as f:
                    json.dump(file_data,f,indent=2)
                    st.rerun()