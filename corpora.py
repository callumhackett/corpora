from collections import Counter
import os
import re
import pandas as pd
import streamlit as st

MAX_RETURNS = 1000 # maximum number of match entries to show in the results table
SOURCE_LIMIT = 20000 # maximum entries in a limited data source

st.set_page_config(page_title="Corpora", layout="wide")

@st.cache_data(max_entries=1)
def compile_data(source):
    """Compile data into a list from source chosen by user in Search Parameters."""
    data = []

    # DROP Questions import
    if source == "DROP Questions":
        with open("data/drop_dataset_train_questions.txt", encoding="utf-8") as f:
            for line in f:
                data.append(line)

    # DROP Contexts import
    if source == "DROP Contexts":
        with open("data/drop_dataset_train_contexts.txt", encoding="utf-8") as f:
            for line in f:
                data.append(line)

    # HotpotQA Questions import
    if source == "HotpotQA Questions":
        with open("data/hotpot_train_v1.1_questions.txt", encoding="utf-8") as f:
            for line in f:
                data.append(line)
    
    # HotpotQA Contexts import
    if source == "HotpotQA Contexts (small)":
        with open("data/hotpot_train_v1.1_contexts_small.txt", encoding="utf-8") as f:
            for line in f:
                data.append(line)
    if source == "HotpotQA Contexts (full)":
        for filename in os.listdir("data"):
            if "hotpot" in filename and "contexts" in filename and "small" not in filename:
                with open(os.path.join("data", filename), encoding="utf-8") as f:
                    for line in f:
                        data.append(line)
    
    # QALD-9 Questions import
    if source == "QALD-9 Questions":
        with open("data/qald-9-train-multilingual_questions.txt", encoding="utf-8") as f:
            for line in f:
                data.append(line)

    # SQuAD2.0 Questions import
    if source == "SQuAD2.0 Questions":
        with open("data/squad_train-v2.0_questions.txt", encoding="utf-8") as f:
            for line in f:
                data.append(line)

    # SQuAD2.0 Contexts import
    if source == "SQuAD2.0 Contexts":
        with open("data/squad_train-v2.0_contexts.txt", encoding="utf-8") as f:
            for line in f:
                data.append(line)

    return data, len(data)

def find_matches(query_re, data):
    """Find, count and return all token matches for a RegEx in each item of a list of strings."""
    match_counts = Counter()
    entry_count = 0
    match_entries = []
    for entry in data:
        match = re.findall(query_re, entry)
        if match:
            entry_count += 1
            for m in match:
                if case_flag == re.IGNORECASE:
                    match_counts[m.lower()] += 1
                else:
                    match_counts[m] += 1
            if len(match_entries) < MAX_RETURNS:
                for m in set(match):
                    entry = re.sub(r"\b" + m + r"\b", '<font color="red"><b>' + m + "</b></font>", entry)
                match_entries.append(entry.strip())
    return match_counts, entry_count, match_entries

# User Interface
parameters, results, statistics = st.columns(spec=[0.2, 0.525, 0.275], gap="large")

with parameters:
    st.markdown("#### Search Parameters")
    source = st.radio("**Source (all training sets)**:", [
        "DROP Questions",
        "DROP Contexts",
        "HotpotQA Questions",
        "HotpotQA Contexts (small)",
        "HotpotQA Contexts (full)*",
        "QALD-9 Questions",
        "SQuAD2.0 Questions",
        "SQuAD2.0 Contexts"
    ])
    st.caption("*not recommended unless you need exact stats due to resource constraints")
    case_sensitive = st.toggle("case-sensitive")
    case_flag = re.IGNORECASE if not case_sensitive else 0
    query = st.text_input("**Search term (\* is a wildcard)**:").strip()

with results:
    st.markdown(f"#### Results")
    st.write("*Select a data source, type a search term, then press Enter*")

with statistics:
    st.markdown("#### Statistics")

# Execution
if query != "":
    # search
    query_re = re.compile(r"\b" + query.replace("*", "[\w|-]+") + r"\b", flags=case_flag)
    data, dataset_size = compile_data(source)
    match_counts, entry_count, match_entries = find_matches(query_re, data)

    # return
    with results:
        if len(match_entries) == MAX_RETURNS:
            st.markdown(f"Because of a large number of matches, the returned results have been capped at {MAX_RETURNS:,}")
        results_table_container = st.container(height=500, border=False)
    with results_table_container.container():
        results_table = pd.DataFrame({"": match_entries})
        st.markdown(results_table.to_html(escape=False, header=False, bold_rows=False), unsafe_allow_html=True)

    # statistics
    with statistics:
        if dataset_size != 0:
            st.markdown(f"{round(100*(entry_count/dataset_size), 2)}% of entries in your source(s) had ≥1 match.")
        st.markdown(f"{len(match_counts):,} unique string(s) had hits:")
        stats_table = pd.DataFrame(
            {"string": match_counts.keys(), "count": match_counts.values()}
        ).sort_values(by=["count", "string"], ascending=False).reset_index(drop=True)
        st.dataframe(stats_table, column_config={"_index": None, "Hit": st.column_config.TextColumn()}, use_container_width=True)
        if source == "HotpotQA Contexts":
            st.caption("""
                    For HotpotQA contexts, each of the multiple contexts per question is counted as one entry. 
                    The headline percentage is a slight underestimate because of some data format issues.
                    """)
