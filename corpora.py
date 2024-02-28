import json
import streamlit as st

"""
with open("hotpot_train_v1.1.json") as f:
    data = json.load(f)
"""

with open("hotpot_train_v1.1_questions.txt", encoding="utf-8") as data:
    questions = [line.rstrip() for line in data]

query = st.text_input('Search term: ').lower()

for q in questions:
    if query != "" and query in q.lower():
        st.markdown(q.replace(query, "**"+query+"**"))