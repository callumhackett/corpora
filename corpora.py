from collections import Counter
import os
import re
import pandas as pd
import streamlit as st

MAX_RETURNS = 1000 # maximum number of match entries to show in the results table

st.set_page_config(page_title="Corpora", layout="wide")

@st.cache_data(max_entries=1) # keep one and only one compiled data source in memory
def compile_data(source):
    """
    Compile data from source into a list of strings.
    Source is chosen by user in Search Parameters.
    """
    data = []
    word_count = 0
    source = ("_").join(source.lower().split())

    with open(os.path.join("data", f"{source}.txt"), encoding="utf-8") as f:
        for line in f:
            data.append(line)
            word_count += len(line.split())

    return data, len(data), word_count

def find_matches(query, data):
    """Find, count and return all token matches for a RegEx in each item of a list of strings."""
    token_counts = Counter()
    entry_counts = 0
    entry_texts = []

    for entry in data:
        match = re.findall(query, entry)
        # count the matches
        if match:
            entry_counts += 1
            for m in match:
                if case_flag == re.IGNORECASE:
                    token_counts[m.lower()] += 1
                else:
                    token_counts[m] += 1
            # add matches to list with HTML styling
            if len(entry_texts) < MAX_RETURNS:
                for m in set(match):
                    entry = re.sub(r"\b" + m + r"\b", '<font color="red"><b>' + m + "</b></font>", entry)
                entry_texts.append(entry.strip())

    return token_counts, entry_counts, entry_texts

# User Interface
parameters, results, statistics = st.columns(spec=[0.2, 0.525, 0.275], gap="large")

# Search Parameters column
with parameters:
    st.markdown("#### Search Parameters")
    source = st.radio("**Source**:", [
        "DROP Questions",
        "DROP Contexts",
        "HotpotQA Questions",
        "HotpotQA Contexts*",
        "QALD-9 Questions",
        "Spoken English†",
        "SQuAD2.0 Questions",
        "SQuAD2.0 Contexts"
    ])
    source = source.replace("*", "").replace("†", "")
    case_sensitive = st.toggle("case-sensitive")
    case_flag = re.IGNORECASE if not case_sensitive else 0
    query = st.text_input("**Search term (use * as a wildcard)**:").strip()
    st.caption(
        """
        *This is a representative subset, as the full set is too large for this tool.\n
        †To compare with writing. Sampled from the British National Corpus.\n
        *All benchmark data is sourced exclusively from training datasets.*
        """
    )

# Results column
with results:
    st.markdown(f"#### Results")
    st.write("*Select a data source, type a search term, then press Enter*")

# Statistics column
with statistics:
    st.markdown("#### Statistics")

# Execution
if query != "":
    # search
    query = re.compile(r"\b" + query.replace("*", "[\w|-]+") + r"\b", flags=case_flag) # convert text query to regex
    source_data, source_entry_count, source_word_count = compile_data(source) # compile data from user-chosen source
    token_counts, entry_counts, entry_texts = find_matches(query, source_data) # extract search results
    token_total = sum(token_counts.values())

    # display results
    with results:
        if not entry_texts:
            st.markdown("There were no results for your search.")
        else:
            if len(entry_texts) == MAX_RETURNS:
                st.markdown(f"Because of a large number of matches, the displayed results have been capped at {MAX_RETURNS:,}")
            results_table_container = st.container(height=500, border=False) # place results inside fixed-height container
            with results_table_container.container():
                results_table = pd.DataFrame({"": entry_texts}) # convert search results to table
                results_table.index += 1 # set row index to start from 1 instead of 0
                st.markdown( # convert pd table to HTML to allow text highlighting
                    results_table.to_html(escape=False, header=False, bold_rows=False), unsafe_allow_html=True
                )

    # display stats
    with statistics:
        if entry_texts:
            entry_proportion = round(100*(entry_counts/source_entry_count), 2) or "<0.01"
            token_proportion = round(100*(token_total/source_word_count), 2) or "<0.01"
            st.markdown(
                f"""
                - Entries with ≥1 match: {entry_proportion}%
                - Proportion of all source text: {token_proportion}%
                - Unique matches: {len(token_counts.keys()):,}
                - Total matches: {token_total:,}
                """
            )
            stats_table = pd.DataFrame( # convert string match data to table
                {"string": token_counts.keys(),
                "count": token_counts.values(),
                "% in set": [round(100*(value/token_total), 2) or "<0.01" for value in token_counts.values()]}
            ).sort_values(by=["count", "string"], ascending=False).reset_index(drop=True)
            stats_table.index += 1 # set row index to start from 1 instead of 0
            st.dataframe(
                stats_table, column_config={"Hit": st.column_config.TextColumn()}, use_container_width=True
            )
            if source == "HotpotQA Contexts":
                st.caption("Each of the multiple contexts per HotpotQA question is counted as one entry.")
            if source == "Spoken English":
                st.caption(
                    """
                    An ‘entry’ in the Spoken English source is roughly a turn in a conversation but some of the 
                    source situations are official meetings and lectures.
                    """)
