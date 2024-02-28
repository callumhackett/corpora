import json
import streamlit as st

"""
with open("hotpot_train_v1.1.json") as f:
    data = json.load(f)
"""

with open("hotpot_train_v1.1_questions.txt", encoding="utf-8") as data:
    questions = [line.rstrip() for line in data]

for q in questions:
    if "Michael" in q:
        st.write(q)