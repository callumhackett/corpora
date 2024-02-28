import json
import streamlit as st

st.markdown("# Corpus Search")

# to do: change sources and present them as something other than dropdown list
# to do: have associated choice for max number of results per source
sources = st.multiselect("Data sources:", ["Questions", "Contexts"])

with open("hotpot_train_v1.1_questions.txt", encoding="utf-8") as data:
    questions = [line.rstrip() for line in data]

query = st.text_input('Search term: ')

if "Questions" in sources:

    st.markdown("# Questions Results")

    for q in questions:
        if query != "" and query.lower() in q.lower():
            st.markdown(q.replace(query, "**"+query+"**"))

if "Contexts" in sources:

    st.write("Context data not ready yet")