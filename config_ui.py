import pandas as pd
from datetime import date
import streamlit as st
import json
import subprocess

# -------------------------------
# Function to write JSON
# -------------------------------


def write_json(new_data, filename='data.json'):
    with open(filename, 'r+') as file:
        file_data = json.load(file)
        file_data["configurations"].append(new_data)
        file.seek(0)
        json.dump(file_data, file, indent=4)


# -------------------------------
# Global state
# -------------------------------
if "process" not in st.session_state:
    st.session_state.process = None

filename = 'data.json'
with open(filename, 'r+') as file:
    file_data = json.load(file)

configurations = file_data["configurations"]

# -------------------------------
# Control buttons
# -------------------------------
col1, col2 = st.columns(2)
with col1:
    start_btn = st.button("▶️ Run Script",
                          disabled=st.session_state.process is not None)
with col2:
    stop_btn = st.button("⏹️ Stop Script",
                         disabled=st.session_state.process is None)

if start_btn:
    st.session_state.process = subprocess.Popen(
        ["python", "wallapop_alerta.py"])
    st.toast("Script started")
    st.rerun()

if stop_btn and st.session_state.process:
    st.session_state.process.terminate()
    st.session_state.process = None
    st.toast("Script stopped")
    st.rerun()

# -------------------------------
# Input lock
# -------------------------------
is_running = st.session_state.process is not None

# Bot and chat connection data
st.title("Search Data")
bot_token_input = st.text_input("Telegram bot token",
                                value=file_data["telegram_token"],
                                disabled=is_running)

telegram_chat_input = st.text_input("Telegram chat id",
                                    value=file_data["telegram_chat_id"],
                                    disabled=is_running)

time = st.number_input("Time between searches in minutes",
                       0, 2880, file_data["time"], 1,
                       disabled=is_running)

st.write(f"Current telegram bot token: {file_data['telegram_token']}")
st.write(f"Current telegram chat id: {file_data['telegram_chat_id']}")
st.write(f"Current time between searches: {file_data['time']}")

button = st.button("Update", disabled=is_running)
if button:
    if bot_token_input:
        file_data["telegram_token"] = bot_token_input
    if telegram_chat_input:
        file_data["telegram_chat_id"] = telegram_chat_input
    if time > 0:
        file_data["time"] = time
    with open('data.json', 'w') as f:
        json.dump(file_data, f, indent=2)
    st.rerun()

# Product form
st.title("Form for adding products")
with st.form("my_form"):
    st.write("Inside the form")
    product_name = st.text_input("Product to search", disabled=is_running)
    min_price = st.number_input(
        "Min price", 0, 16777216, 0, 1, disabled=is_running)
    max_price = st.number_input(
        "Max price", 0, 16777216, 0, 1, disabled=is_running)

    submitted = st.form_submit_button("Submit", disabled=is_running)
    if submitted:
        if max_price >= min_price:
            if product_name:
                product_dict = {
                    "keywords": product_name,
                    "min": min_price,
                    "max": max_price
                }
                write_json(product_dict)
                st.rerun()
            else:
                st.write("You need to enter a product name")
        else:
            st.write("Maximum price cannot be lower than the minimum price")

# Product list
st.title("Current products")
for i, config in enumerate(configurations):
    with st.container(border=True):
        st.markdown(f"**{config['keywords']}**")
        st.markdown(f"Min price: {config['min']}")
        st.markdown(f"Max price: {config['max']}")
        delete_button = st.button("❌ Delete",
                                  key=f"delete_{i}",
                                  disabled=is_running)
        if delete_button:
            configurations.pop(i)
            file_data["configurations"] = configurations
            with open('data.json', 'w') as f:
                json.dump(file_data, f, indent=2)
                st.rerun()
