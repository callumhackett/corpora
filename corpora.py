import json
import streamlit as st

"""
with open("hotpot_train_v1.1.json") as f:
    data = json.load(f)
"""

with open("hotpot_train_v1.1_questions.txt", encoding="utf-8") as questions:
    data = questions.read()

st.write(data)