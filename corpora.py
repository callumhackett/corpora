from collections import Counter
import json
import re
import pandas as pd
import streamlit as st

DATASETS = ["HotpotQA Full", "HotpotQA Questions", "HotpotQA Contexts"]
DATASET_SIZES = {"HotpotQA Questions":90447, "HotpotQA Contxts":899667}

def compile_data(source):
    data = []
    if source in ["HotpotQA Full", "HotpotQA Questions"]:
        with open("data/hotpot_train_v1.1_questions.txt", encoding="utf-8") as f:
            for line in f:
                data.append(line)
    if source in ["HotpotQA Full", "HotpotQA Contexts"]:
        with open("data/hotpot_train_v1.1_contexts1.txt", encoding="utf-8") as f:
            for line in f:
                data.append(line)
    return data

def find_matches(query, case_flag, data):
    query_re = re.compile(r"\b" + query + r"\b", flags=case_flag)
    match_counts = Counter()
    match_contexts = []
    for entry in data:
        match = re.findall(query_re, entry)
        if match:
            for m in match:
                if case_flag == re.IGNORECASE:
                    match_counts[m.lower()] += 1
                else:
                    match_counts[m] += 1
            match_contexts.append(entry)
    return match_counts, match_contexts

# User Interface
st.markdown("### Corpus Search")
source = st.radio("**Data source**:", DATASETS)
data = compile_data(source)
query = st.text_input("**Search term (use * as a wildcard):**").strip().replace("*", "[\w|-]+")
case_sensitive = st.toggle("case-sensitive")
case_flag = re.IGNORECASE if not case_sensitive else 0

if query != "":
    # matches
    match_counts, match_contexts = find_matches(query, case_flag, data)
    match_strings = len(match_counts)
    entry_count = len(match_contexts)
    dataset_size = DATASET_SIZES[source]

    # stats
    string_stats = pd.DataFrame(
        {"match": match_counts.keys(), "count": match_counts.values()}
    ).sort_values(by=["count", "match"], ascending=False).reset_index(drop=True)
    st.dataframe(string_stats, column_config={"Hit": st.column_config.TextColumn()})

    # results
    st.markdown(f"#### Results")
    st.markdown(f"*There are matches in {entry_count} of the {DATASET_SIZES[source]} entries in your chosen data source ({round(100*(entry_count/dataset_size), 2)}%)*")
    for context in match_contexts:
        st.write(context)
