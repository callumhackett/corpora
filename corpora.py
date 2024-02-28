import json
import re
import streamlit as st

st.markdown("# Corpus Search")

# to do: change sources and present them as something other than dropdown list
# to do: have associated choice for max number of results per source
sources = st.multiselect("Data sources:", ["Questions", "Contexts"])

with open("hotpot_train_v1.1_questions.txt", encoding="utf-8") as data:
    questions = [line.rstrip() for line in data]

query = st.text_input('Search term: ')
query_re = re.compile(r"\b" + query + r"\b", flags=re.IGNORECASE)
case_insensitive = st.toggle('Ignore case')
case_flag = re.IGNORECASE if case_insensitive else 0

query = st.text_input('Search term: ').strip().replace("*", "\w+")
query_re = re.compile(r"\b" + query + r"\b", flags=case_flag)

if "Questions" in sources:

    st.markdown("# Questions Results")

    for q in questions:
        match = re.search(query_re, q)
        if query != "" and match:
            st.markdown(re.sub(query, "**"+match.group(0)+"**", q, flags=re.IGNORECASE))

if "Contexts" in sources:

    st.write("Context data not ready yet")