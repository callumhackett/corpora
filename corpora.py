from collections import Counter
import json
import re
import pandas as pd
import streamlit as st

DATASETS = ["HotpotQA Full", "HotpotQA Questions", "HotpotQA Contexts"]

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
    matches = []
    match_count = 0
    for entry in data:
        match = re.findall(query_re, entry)
        if match:
            matches.append((match, entry))
            match_count += len(match)
    return matches, match_count

# User Interface
st.markdown("### Corpus Search")
source = st.radio("**Data source**:", DATASETS)
data = compile_data(source)
query = st.text_input("Search term (use * as a wildcard):").strip().replace("*", "(\w|-)+")
case_sensitive = st.toggle("case-sensitive")
case_flag = re.IGNORECASE if not case_sensitive else 0

if query != "":
    # matches
    matches, match_count = find_matches(query, case_flag, data)
    matches_per_entry = [match[0] for match in matches]
    matches_compiled = []
    for batch in matches_per_entry:
        for match in batch:
            matches_compiled.append(match)
    if not case_sensitive:
        all_hits = [t.lower() for t in all_hits]

    # stats
    hit_counts = Counter(all_hits)
    num_unique_hits = len(hit_counts)
    hit_df = pd.DataFrame(
        {"Hit": hit_counts.keys(), "Count": hit_counts.values()}
    ).sort_values(by=["Count", "Hit"], ascending=False).reset_index(drop=True)

    st.markdown(f"Unique hits: {len(hit_df)}")
    st.dataframe(hit_df, column_config={"Hit": st.column_config.TextColumn()})
    st.dataframe(hit_df["Count"].describe().to_frame().transpose()[["mean", "std", "min", "max"]])

    # results
    st.markdown(f"#### Results ({match_count})")
    for hits, original_str in matches:
        for single_hit in hits:
            original_str = re.sub(
                single_hit,
                "<u>"+single_hit+"</u>",
                original_str
            )
        st.markdown(
            original_str,
            unsafe_allow_html=True
        )
