from collections import Counter
import os
import re
import pandas as pd
import streamlit as st

CACHE_SIZE = 1 # number of compiled corpora to keep in memory; more than 1 may cause issues over the web
DATA_FOLDER = "data" # folder with .txt files of line-separated corpus data; filenames will be used in user selection
HOTPOTQA_NOTICE = (
    """
    The HotpotQA dataset has been filtered for contexts and questions labelled "hard", as the test set contains only 
    cases of this kind.
    """
)
MAX_RETURNS = 1000 # maximum number of examples to show in the main results table

@st.cache_data(max_entries=CACHE_SIZE)
def compile_corpus(corpus_name):
    """
    Compile corpus data from a .txt source of line-separated entries into a list of strings.
    The source is chosen by the user in Search Parameters.
    """
    corpus_name = corpus_name.replace(" ", "_") # match source name with filename
    data = [] # initialise the list of corpus entries
    vocab = Counter() # initialise a full vocab count
    punctuation = re.compile(r'[,;!/:\(\)\.\?"\[\]]') # define punctuation to enable accurate vocab counts

    with open(os.path.join(DATA_FOLDER, f"{corpus_name}.txt"), encoding="utf-8") as f:
        for line in f: # for each entry in the corpus
            data.append(line) # add it to the list
            line = re.sub(punctuation, "", line) # remove punctuation to facilitate vocab counts
            for word in line.split(): # for each token in the entry
                if word.isalpha(): # if it's alphabetical
                    vocab[word.lower()] += 1 # add to its vocab count

    entry_count = len(data) # the number of entries in the corpus
    vocab_size = len(vocab) # the number of unique words in the corpus
    word_count = sum(vocab.values()) # the number of word tokens in the corpus

    return data, entry_count, vocab, vocab_size, word_count

def find_matches(query, data):
    """
    Find, count and return all matches for a RegEx in each string in a list.
    The RegEx should not contain groups (a constraint to allow the interface to be used by non-coders).
    """
    entry_count = 0 # initialise count of entries containing ≥1 match
    token_counts = Counter() # initialise count of matching tokens
    entry_texts = [] # initialise list of entries containing matches

    for entry in data: # for each string in the list
        match = re.findall(query, entry) # search for matches
        if match: # if there are any matches
            entry_count += 1 # increase the count of matching entries
            for m in match: # for each matching token
                # add to the token counts, respecting case-sensitivity
                if case_flag == re.IGNORECASE:
                    token_counts[m.lower()] += 1
                else:
                    token_counts[m] += 1
            if len(entry_texts) < MAX_RETURNS: # if number of recorded entries is not at results cap
                for m in set(match): # for each unique matching string
                    # add HTML styling to the occurrences of the match in the entry
                    entry = re.sub(r"\b" + m + r"\b", '<font color="red"><b>' + m + "</b></font>", entry)
                entry_texts.append(entry.strip()) # add the styled entry to the match list

    return entry_count, token_counts, entry_texts

# User Interface
st.set_page_config(page_title="Corpora", layout="wide") # browser tab title and page layout; must be first st call
corpus_filenames = sorted( # determine corpus source options for the user based on filenames in DATA_FOLDER
    [f.rstrip(".txt").replace("_", " ") for f in os.listdir(DATA_FOLDER) if f.endswith(".txt")]
)
parameters, results, statistics = st.columns(spec=[0.2, 0.525, 0.275], gap="large") # columns with widths and gap size

# Search Parameters column
with parameters:
    st.markdown("#### Search Parameters")
    source = st.radio("**Source**:", corpus_filenames) # radio buttons for corpus sources
    st.caption("*All benchmark data is sourced exclusively from training datasets*")
    case_sensitive = st.toggle("case-sensitive")
    case_flag = re.IGNORECASE if not case_sensitive else 0
    query = st.text_input("**Search term**:").strip()
    st.caption("Use * as a wildcard and ^ to match the start of an entry")
    # compile a corpus whenever a new radio button is selected
    corpus_data, corpus_entry_count, corpus_vocab, corpus_vocab_size, corpus_word_count = compile_corpus(source)

# Results column
with results:
    st.markdown(f"#### Results")
    st.write("*Select a data source, type a search term, then press Enter*")

# Statistics column
with statistics:
    st.markdown("#### Statistics")
    search_stats, corpus_stats = st.tabs(["Search Stats", "Corpus Stats"])

with corpus_stats:
    st.markdown(
        f"""
        - Entries: {corpus_entry_count:,}
        - Vocab size: {corpus_vocab_size:,}
        - Word count: {corpus_word_count:,}
        """)
    if source.startswith("HotpotQA"):
        st.caption(HOTPOTQA_NOTICE)
    st.markdown("Top 1,000 Vocab Items:")
    vocab_table = pd.DataFrame( # convert string match data to table
        {"word": corpus_vocab.keys(),
        "count": corpus_vocab.values(),
        "% in source": [round(100*(value/corpus_word_count), 2) or "<0.01" for value in corpus_vocab.values()]}
    ).sort_values(by=["count", "word"], ascending=False).reset_index(drop=True)
    vocab_table.index += 1 # set row index to start from 1 instead of 0
    st.dataframe(vocab_table[:1000], use_container_width=True)
    if source == "Spoken English":
        st.caption(
            """
            The Spoken English source is a sample of the spoken portion of the British National Corpus and is offered as 
            a naturalistic point of comparison against written texts.
            """
        )

# Execute a search when a query is confirmed
if query != "":
    # prohibit search terms that can cause conflicts with the RegEx mechanics
    if re.search(r'[\\\(\)\[\]\?\$\+]', query):
        with results:
            st.markdown(
                """
                ⚠️ Having certain non-alphabetic characters in your search term can cause errors because of the way the
                search function works under the hood, so this search was not run. If you need results for your query or 
                you just want to search with regular expressions, let me know.
                """
            )
    elif query in ["*", "^"]:
        with results:
            st.markdown(
                """
                ⚠️ You can use wildcards but you need to use them *with* something: other words or even just more 
                wildcards. If you want to search for a single wildcard to get a vocab list, check the 'Corpus Stats' 
                tab under 'Statistics'.
                """
            )
    else:
        query = query.replace("*", "[\w\",'-]+").replace(".", "\.") # convert user-facing wildcard to RegEx pattern
        query_re = re.compile(r"\b" + query + r"\b", flags=case_flag) # compile query as RegEx
        entry_count, token_counts, entry_texts = find_matches(query_re, corpus_data) # extract search results
        token_total = sum(token_counts.values())

        # display results
        with results:       
            if not entry_texts:
                st.markdown("There were no results for your search.")
            else:
                if len(entry_texts) == MAX_RETURNS:
                    st.markdown(
                        f"""
                        Because of a large number of matches, the displayed results have been capped at 
                        {MAX_RETURNS:,}
                        """
                    )
                results_table_container = st.container(height=500, border=False) # place results in fixed-height box
                with results_table_container.container():
                    results_table = pd.DataFrame({"": entry_texts}) # convert search results to table
                    results_table.index += 1 # set row index to start from 1 instead of 0
                    st.markdown( # convert pd table to HTML to allow text highlighting
                        results_table.to_html(escape=False, header=False, bold_rows=False), unsafe_allow_html=True
                    )

        # display stats
        with search_stats:
            if entry_texts:
                entry_proportion = round(100*(entry_count/corpus_entry_count), 2) or "<0.01"
                token_proportion = min(100.0, round(100*(token_total/corpus_word_count), 2)) or "<0.01"
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
                    st.caption(HOTPOTQA_NOTICE)
                if source == "Spoken English":
                    st.caption(
                        """
                        An ‘entry’ in the Spoken English source is roughly a turn in a conversation but this is 
                        situation-specific.
                        """
                    )
