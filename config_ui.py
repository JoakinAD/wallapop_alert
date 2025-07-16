import pandas as pd
from datetime import date
import streamlit as st
st.title(f"Search Data")

configurations = [{
      "keywords": "steam deck oled",
      "min": 100,
      "max": 350
    },
    {
      "keywords": "rog ally",
      "min": 100,
      "max": 400
    }]
products = []
mins = []
maxs = []

for product in configurations:
    products.append(product["keywords"])
    mins.append(product["min"])
    maxs.append(product["max"])

bot_token_input = st.text_input("Telegram bot token")
telegram_chat_input = st.text_input("Telegram chat id")
time = st.number_input("Time between searches in minutes", 0, 2880, "min", 1)

st.write(f"Actual telegram bot token: {bot_token_input}")
st.write(f"Actual telegram chat id: {telegram_chat_input}")
st.write(f"Actual time between searches: {time}")
button = st.button("Enter")

st.title(f"Form for adding products")
with st.form("my_form"):
    st.write("Inside the form")
    product_name = st.text_input("Product to search")
    min = st.number_input("Min price", 0, 16777216, "min", 1)
    max = st.number_input("Max price", 0, 16777216, "min", 1)

    submitted = st.form_submit_button("Submit")
    if submitted:
        if max >= min:
            if product:
                product_dict = {
                    "keywords": product,
                    "min": min,
                    "max": max
                }
                configurations.append(product_dict)
                st.write(f"Product added")
            else:
                st.write(f"You need to enter a product name")
        else:
            st.write("Maximum price cant be over the minimum price")

st.title("Actual products")

for i, product in enumerate(configurations):
        with st.container(border=True):
            st.markdown(f"**{product['keywords']}**")
            st.markdown(f"Min price: {product['min']}")
            st.markdown(f"Man price: {product['max']}")
            delete_button = st.button("❌ Eliminar", key=f"delete_{i}")
            if delete_button:
                configurations.pop(i)
