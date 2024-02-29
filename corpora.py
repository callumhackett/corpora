from collections import Counter
import os
import re
import pandas as pd
import streamlit as st

DATASET_SIZES = {"HotpotQA Questions":90447, "HotpotQA Contexts":899667}
RESULTS_PER_PAGE = 10

st.set_page_config(page_title="Corpora", layout="wide")
if "page" not in st.session_state:
    st.session_state["page"] = 0

@st.cache_data
def compile_data(sources):
    """Compile data into a single list from sources chosen by checkbox."""
    data = []
    if "HotpotQA Questions" in sources:
        with open("data/hotpot_train_v1.1_questions.txt", encoding="utf-8") as f:
            for line in f:
                data.append(line)
    if "HotpotQA Contexts" in sources:
        for filename in os.listdir("data"):
            if "hotpot" in filename and "contexts" in filename:
                with open(os.path.join("data", filename), encoding="utf-8") as f:
                    for line in f:
                        data.append(line)
    return data

@st.cache_data
def find_matches(query_re, data):
    count = 1
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
            for m in set(match):
                entry = entry.replace(m, ":red[**" + m + "**]")
            match_contexts.append(str(count) + entry)
            count += 1
    return match_counts, match_contexts

def reset_page():
    st.session_state["page"] = 0

def write_results_batch(data, page):
    start_index = page * RESULTS_PER_PAGE
    end_index = min(start_index + RESULTS_PER_PAGE, len(data))
    for match in data[start_index:end_index]:
        st.write(match)
    if len(data[start_index:]) > RESULTS_PER_PAGE:   
        if st.button("Load more", key=st.session_state["page"]):
            st.session_state["page"] += 1
            with results.container():
                write_results_batch(data, st.session_state["page"])

column1, column2, column3 = st.columns(spec=[0.2, 0.5, 0.3], gap="large")

# User Interface
with column1:
    st.markdown("#### Search Settings")
    st.markdown("**Sources**:")
    sources = []
    if st.checkbox("HotpotQA Questions", on_change=reset_page):
        sources.append("HotpotQA Questions")
    if st.checkbox("HotpotQA Contexts"):
        sources.append("HotpotQA Contexts", on_change=reset_page)
    case_sensitive = st.toggle("case-sensitive search", on_change=reset_page)
    case_flag = re.IGNORECASE if not case_sensitive else 0
    query = st.text_input("**Search term (use * as a wildcard):**", on_change=reset_page).strip().replace("*", "[\w|-]+")
    st.caption("*only training sets are used in this tool*")

with column2:
    st.markdown(f"#### Results")
    st.write("*Select a data source, type a search term, then press Enter*")
    results = st.empty()

if query.strip() != "":
    # matches
    query_re = re.compile(r"\b" + query + r"\b", flags=case_flag)
    data = compile_data(sources)
    match_counts, match_contexts = find_matches(query_re, data)
    match_strings = len(match_counts)
    entry_count = len(match_contexts)
    dataset_size = 0
    for key in sources:
        dataset_size += DATASET_SIZES[key]

    # results
    with results.container():
        write_results_batch(match_contexts, st.session_state["page"])

    # statistics
    with column3:
        st.markdown("#### Statistics")
        st.markdown(f"""
                    {round(100*(entry_count/dataset_size), 2)}% of entries in your source(s) had ≥1 match.\n
                    {len(match_counts):,} unique string(s) were matched:
                    """
                    )
        string_stats = pd.DataFrame(
            {"string": match_counts.keys(), "count": match_counts.values()}
        ).sort_values(by=["count", "string"], ascending=False).reset_index(drop=True)
        st.dataframe(string_stats, column_config={"Hit": st.column_config.TextColumn()}, use_container_width=True)
        st.caption("""
                   For HotpotQA, each of the multiple contexts per question counts as one entry. 
                   The headline percentage is a slight underestimate when contexts are included because of some data formatting issues.
                   """)
