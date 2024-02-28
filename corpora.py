from collections import Counter
import json
import re
import streamlit as st

st.markdown("# Corpus Search")

# to do: change sources and present them as something other than dropdown list
# to do: have associated choice for max number of results per source
sources = st.multiselect("Data sources:", ["Questions", "Contexts"])

with open("hotpot_train_v1.1_questions.txt", encoding="utf-8") as data:
    questions = [line.rstrip() for line in data]

num_questions = len(questions)

case_sensitive = st.toggle('Case sensitive')
case_flag = re.IGNORECASE if not case_sensitive else 0

query = st.text_input('Search term: ').strip().replace("*", "\w+")
query_re = re.compile(r"\b" + query + r"\b", flags=case_flag)

if "Questions" in sources:

    matches = []
    match_count = 0

    for q in questions:
        match = re.search(query_re, q)
        if query != "" and match:
            match_count += 1
            matches.append((match.group(0), q))

    st.markdown(f"### Questions Results ({match_count})")
    for m in matches:
        st.markdown(
            re.sub(
                query_re,
                "<u>"+m[0]+"</u>",
                m[1]
            ),
            unsafe_allow_html=True
        )

if "Contexts" in sources:

    st.write("Context data not ready yet")