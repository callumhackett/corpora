from collections import Counter
import os
import re
import pandas as pd
import streamlit as st

MAX_RETURNS = 1000 # maximum number of match entries to show in the results table
SOURCE_LIMIT = 20000 # maximum entries in a limited data source

st.set_page_config(page_title="Corpora", layout="wide")

@st.cache_data(max_entries=1)
def compile_data(source, limit=False):
    """Compile data into a list from source chosen by user in Search Parameters."""
    data = []

    # HotpotQA Questions import
    if source == "HotpotQA Questions":
        with open("data/hotpot_train_v1.1_questions.txt", encoding="utf-8") as f:
            for line in f:
                #if limit and len(data) == SOURCE_LIMIT:
                if len(data) == SOURCE_LIMIT
                    break
                data.append(line)
    
    # HotpotQA Contexts import
    elif source == "HotpotQA Contexts":
        for filename in os.listdir("data"):
            if "hotpot" in filename and "contexts" in filename:
                with open(os.path.join("data", filename), encoding="utf-8") as f:
                    for line in f:
                        #if limit and len(data) == SOURCE_LIMIT:
                        if len(data) == SOURCE_LIMIT:
                            break
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
    source = st.radio("**Source**:", ["HotpotQA Questions", "HotpotQA Contexts"])
    corpus_subset = st.toggle("limit source size")
    case_sensitive = st.toggle("case-sensitive search")
    case_flag = re.IGNORECASE if not case_sensitive else 0
    query = st.text_input("**Search term (use * as a wildcard):**").strip().replace("*", "[\w|-]+")
    st.caption("*only training data is used in this tool*")

with results:
    st.markdown(f"#### Results")
    st.write("*Select a data source, type a search term, then press Enter*")

with statistics:
    st.markdown("#### Statistics")

# Execution
if query != "":
    # search
    query_re = re.compile(r"\b" + query + r"\b", flags=case_flag)
    data, dataset_size = compile_data(source, limit=corpus_subset)
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
