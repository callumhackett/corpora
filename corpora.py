import json
import streamlit as st

st.markdown("# Corpus Search")

with open("hotpot_train_v1.1_questions.txt", encoding="utf-8") as data:
    questions = [line.rstrip() for line in data]

query = st.text_input('Search term: ')

for q in questions:
    if query != "" and query.lower() in q.lower():
        st.markdown(q.replace(query, "**"+query+"**"))