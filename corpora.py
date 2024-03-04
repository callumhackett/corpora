from collections import Counter
import os
import re
import pandas as pd
import streamlit as st

MAX_RETURNS = 1000 # maximum number of match entries to show in the results table

st.set_page_config(page_title="Corpora", layout="wide") # browser tab title and page layout

@st.cache_data(max_entries=1) # keep one and only one compiled data source in memory
def compile_data(source):
    """
    Compile data from a line-separated .txt source into a list of strings.
    The source is chosen by the user in Search Parameters.
    """
    data = []
    vocab = Counter()
    source = ("_").join(source.lower().split())
    punctuation = re.compile(r'[,;!/:\(\)\.\?"\[\]]')

    with open(os.path.join("data", f"{source}.txt"), encoding="utf-8") as f:
        for line in f:
            data.append(line)
            line = line.replace("-", " ") # separate hyphenations for raw vocab counts
            line = re.sub(punctuation, "", line) # remove punctuation for raw vocab counts
            for word in line.split():
                if word.isalpha(): # only count words as vocab items
                    vocab[word.lower()] += 1

    entry_count = len(data) # calculate the number of entries in the source
    vocab_size = len(vocab) # calculate the number of unique vocab items in the source
    word_count = sum(vocab.values()) # calculate the number of tokens in the source

    return data, entry_count, vocab, vocab_size, word_count

def find_matches(query, data):
    """
    Find, count and return all token matches for a RegEx in each item of a list of strings.
    It is assumed that the RegEx does not contain groups.
    """
    token_counts = Counter()
    entry_count = 0
    entry_texts = []

    for entry in data:
        match = re.findall(query, entry)
        # count the matches
        if match:
            entry_count += 1
            for m in match:
                if case_flag == re.IGNORECASE:
                    token_counts[m.lower()] += 1
                else:
                    token_counts[m] += 1
            # add matches to list for displaying with HTML styling
            if len(entry_texts) < MAX_RETURNS:
                for m in set(match):
                    entry = re.sub(r"\b" + m + r"\b", '<font color="red"><b>' + m + "</b></font>", entry)
                entry_texts.append(entry.strip())

    return token_counts, entry_count, entry_texts

# User Interface
parameters, results, statistics = st.columns(spec=[0.2, 0.525, 0.275], gap="large")

# Search Parameters column
with parameters:
    st.markdown("#### Search Parameters")
    source = st.radio("**Source**:", [
        "DROP Questions",
        "DROP Contexts",
        "HotpotQA Questions",
        "HotpotQA Contexts",
        "QALD-9 Questions",
        "Spoken English",
        "SQuAD2.0 Questions",
        "SQuAD2.0 Contexts"
    ])
    case_sensitive = st.toggle("case-sensitive")
    case_flag = re.IGNORECASE if not case_sensitive else 0
    query = st.text_input("**Search term**:").strip()
    st.caption(
        """
        Use * as a wildcard and ^ to match the start of an entry
        """
    )
    st.caption(
        """
        *All benchmark data is sourced exclusively from training datasets*
        """
    )

    source_data, source_entry_count, source_vocab, source_vocab_size, source_word_count = compile_data(source)

# Results column
with results:
    st.markdown(f"#### Results")
    st.write("*Select a data source, type a search term, then press Enter*")

# Statistics column
with statistics:
    st.markdown("#### Statistics")
    search_stats, source_stats = st.tabs(["Search Stats", "Source Stats"])

with source_stats:
    st.markdown(
        f"""
        - Entries: {source_entry_count:,}
        - Vocab size: {source_vocab_size:,}
        - Word count: {source_word_count:,}
        """)
    st.markdown("Top 1,000 Vocab Items:")
    vocab_table = pd.DataFrame( # convert string match data to table
        {"word": source_vocab.keys(),
        "count": source_vocab.values(),
        "% in source": [round(100*(value/source_word_count), 2) or "<0.01" for value in source_vocab.values()]}
    ).sort_values(by=["count", "word"], ascending=False).reset_index(drop=True)
    vocab_table.index += 1 # set row index to start from 1 instead of 0
    st.dataframe(vocab_table[:1000], use_container_width=True)
    if source == "HotpotQA Contexts":
        st.caption(
            """
            The HotpotQA Contexts dataset is much larger than the others and this can cause slow search times and 
            resource issues. The dataset loaded in this tool (and described above) is a representative subset. If you 
            want more exact results, let me know.
            """
        )
    if source == "Spoken English":
        st.caption(
            """
            The Spoken English source is a sample of the spoken portion of the British National Corpus and is offered as 
            a naturalistic point of comparison against written texts.
            """
        )

# Execution
if query != "":
    if re.search(r'[\\\(\)\[\]\?\$\+]', query):
        with results:
            st.markdown(
                """
                ⚠️ Having certain non-alphabetic characters in your search term can cause errors because of the way the
                search function works under the hood, so this search was not run. If you need results for your query or 
                you just want to search with regular expressions, let me know.
                """
            )
    elif query == "*":
        with results:
            st.markdown(
                """
                ⚠️ You can use wildcards but you need to use them *with* something: other words or even just more 
                wildcards. If you want to search for a single wildcard to get a vocab list, check the 'Source Stats' 
                tab under 'Statistics'.
                """
            )
    else: # search
        query = query.replace("*", "[\w|-]+").replace(".", "\.")
        query_re = re.compile(r"\b" + query + r"\b", flags=case_flag) # convert text query to regex
        token_counts, entry_count, entry_texts = find_matches(query_re, source_data) # extract search results
        token_total = sum(token_counts.values())

        # display results
        with results:       
            if not entry_texts:
                st.markdown("There were no results for your search.")
            else:
                if len(entry_texts) == MAX_RETURNS:
                    st.markdown(
                        f"Because of a large number of matches, the displayed results have been capped at {MAX_RETURNS:,}"
                    )
                results_table_container = st.container(height=500, border=False) # place results inside fixed-height container
                with results_table_container.container():
                    results_table = pd.DataFrame({"": entry_texts}) # convert search results to table
                    results_table.index += 1 # set row index to start from 1 instead of 0
                    st.markdown( # convert pd table to HTML to allow text highlighting
                        results_table.to_html(escape=False, header=False, bold_rows=False), unsafe_allow_html=True
                    )

        # display stats
        with search_stats:
            if entry_texts:
                entry_proportion = round(100*(entry_count/source_entry_count), 2) or "<0.01"
                token_proportion = min(100.0, round(100*(token_total/source_word_count), 2)) or "<0.01"
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
                    "% in set": [str(round(100*(value/token_total), 2) or "<0.01") for value in token_counts.values()]}
                ).sort_values(by=["count", "string"], ascending=False).reset_index(drop=True)
                stats_table.index += 1 # set row index to start from 1 instead of 0
                st.dataframe(stats_table, use_container_width=True)
                if source == "HotpotQA Contexts":
                    st.caption("Each of the multiple contexts per HotpotQA question is counted as one entry.")
                if source == "Spoken English":
                    st.caption(
                        """
                        An ‘entry’ in the Spoken English source is roughly a turn in a conversation but this is 
                        situation-specific.
                        """)
