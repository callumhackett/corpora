from collections import Counter
import os
import re
import pandas as pd
import streamlit as st

LIMIT_DIVISOR = 50 # factor by which to reduce the corpus size to improve search speed

st.set_page_config(page_title="Corpora", layout="wide")

@st.cache_data(max_entries=1)
def compile_data(sources, limit=True):
    """Compile data into a single list from sources chosen by checkboxes in Search Parameters."""
    data = []
    if "HotpotQA Questions" in sources:
        with open("data/hotpot_train_v1.1_questions.txt", encoding="utf-8") as f:
            count = 0
            if limit or not limit:
                for line in f:
                    if count % LIMIT_DIVISOR == 0:
                        data.append(line)
                    count += 1
            else:
                for line in f:
                    data.append(line)
    if "HotpotQA Contexts" in sources:
        for filename in os.listdir("data"):
            if "hotpot" in filename and "contexts" in filename:
                with open(os.path.join("data", filename), encoding="utf-8") as f:
                    count = 0
                    if limit or not limit:
                        for line in f:
                            if count % LIMIT_DIVISOR == 0:
                                data.append(line)
                            count += 1
                    else:
                        for line in f:
                            data.append(line)
    st.write(len(data))
    return data, len(data)

def find_matches(query_re, data):
    """Find and count all individual matches for a RegEx in each data entry."""
    match_counts = Counter()
    match_entries = []
    for entry in data:
        match = re.findall(query_re, entry)
        if match:
            for m in match:
                if case_flag == re.IGNORECASE:
                    match_counts[m.lower()] += 1
                else:
                    match_counts[m] += 1
            for m in set(match):
                entry = re.sub(r"\b" + m + r"\b", '<font color="red"><b>' + m + "</b></font>", entry)
            match_entries.append(entry.strip())
    return match_counts, match_entries

parameters, results, statistics = st.columns(spec=[0.2, 0.525, 0.275], gap="large")

# Main User Interface
with parameters:
    st.markdown("#### Search Parameters")
    st.markdown("**Sources**:")
    sources = []
    if st.checkbox("HotpotQA Questions"):
        sources.append("HotpotQA Questions")
    if st.checkbox("HotpotQA Contexts"):
        sources.append("HotpotQA Contexts")
    case_sensitive = st.toggle("case-sensitive search")
    corpus_subset = st.toggle("corpus subset (less data; faster search)")
    case_flag = re.IGNORECASE if not case_sensitive else 0
    query = st.text_input("**Search term (use * as a wildcard):**").strip().replace("*", "[\w|-]+")
    st.caption("*only training data is used in this tool*")

with results:
    st.markdown(f"#### Results")
    st.write("*Select a data source, type a search term, then press Enter*")
    results_container = st.container(height=500, border=False)

with statistics:
    st.markdown("#### Statistics")

# Search Execution
if query != "":
    # search
    query_re = re.compile(r"\b" + query + r"\b", flags=case_flag)
    data, dataset_size = compile_data(sources, limit=corpus_subset)
    match_counts, match_entries = find_matches(query_re, data)

    # return
    with results_container.container():
        results_table = pd.DataFrame({"": match_entries[:10000]})
        st.markdown(results_table.to_html(escape=False, header=False, bold_rows=False), unsafe_allow_html=True)

    # statistics
    with statistics:
        entry_count = len(match_entries)
        if dataset_size != 0:
            st.markdown(f"{round(100*(entry_count/dataset_size), 2)}% of entries in your source(s) had ≥1 match.")
        if entry_count > 10000:
            st.markdown(f"Because of the large number of matches, the returned texts have been capped at 10,000.")
        st.markdown(f"{len(match_counts):,} unique string(s) had hits:")
        stats_table = pd.DataFrame(
            {"string": match_counts.keys(), "count": match_counts.values()}
        ).sort_values(by=["count", "string"], ascending=False).reset_index(drop=True)
        st.dataframe(stats_table, column_config={"_index": None, "Hit": st.column_config.TextColumn()}, use_container_width=True)
        if "HotpotQA Contexts" in sources:
            st.caption("""
                    For HotpotQA contexts, each of the multiple contexts per question is counted as one entry. 
                    The headline percentage is a slight underestimate because of some data format issues.
                    """)
