import os
import re
from collections import Counter

import pandas as pd
import streamlit as st

CACHE_SIZE = 1 # number of compiled corpora to keep in memory
DATA_FOLDER = "data" # folder with .tsv files of line-separated corpus text and complexity scores
HOTPOTQA_NOTICE = (
    """
    The HotpotQA dataset has been filtered for contexts and questions labelled "hard", as the test set contains only 
    cases of this kind.
    """
)
MAX_RETURNS = 1000 # maximum number of examples to show in the main results table

@st.cache_data(max_entries=CACHE_SIZE)
def compile_corpus(source):
    """
    Compile corpus data from a .tsv source with corpus texts and complexity scores.

    The source is chosen by the user in Search Parameters. User options are derived from filenames.

    Args:
        source: the name of the dataset (determined by user selection)
    """
    corpus_data = [] # initialise the corpus
    vocab = Counter() # initialise a vocab count
    punctuation = re.compile(r'[,;!/:\(\)\.\?"\[\]]') # define punctuation to enable accurate vocab count

    with open(os.path.join(DATA_FOLDER, f"{source.replace(' ', '_')}.tsv"), encoding="utf-8") as f:
        next(f) # skip the header
        for line in f:
            line = line.split("\t")
            corpus_data.append({"text":line[0], "score":float(line[1])})
            # count the vocab, correcting for punctuation
            for word in re.sub(punctuation, "", line[0]).split():
                if word.isalpha():
                    vocab[word.lower()] += 1

    return corpus_data, vocab


def find_matches(query, complexity_range, corpus):
    """
    Find, count and return all matches for a RegEx in each text of the corpus and the subset of the corpus matching the complexity range.
    
    The RegEx should not contain groups (a constraint to allow the interface to be used by non-coders).

    Args:
        query: a RegEx pattern
        complexity_range: a tuple of the min and max complexity values to filter by
        data: a dict with keys "text" and "score"
    """
    dataset_matches = Counter() # initialise a count of entries in the whole dataset with ≥1 match
    in_range_matches = Counter() # initialise a count of entries in the complexity range with ≥1 match
    display_texts = [] # initialise a list of matching entries to display (capped at MAX_RETURNS)

    for entry in corpus:
        text = entry["text"] # set the text to search
        score = entry["score"] # set the score of the text
        in_range = score >= complexity_range[0] and score <= complexity_range[1] # Boolean for in range
        match = re.findall(query, text) # search the text for matches
        if match:
            for m in set([m.lower() for m in match]): # add to whole dataset count
                dataset_matches[m] += 1
            if in_range:
                for m in set([m.lower() for m in match]): # add to complexity range count
                    in_range_matches[m] += 1
            # filter the matches that are displayed by length cap and complexity
            if len(display_texts) < MAX_RETURNS and in_range:
                for m in set(match):
                    # add HTML styling to matches in the original text
                    text = re.sub(r"\b" + m + r"\b", '<font color="red"><b>' + m + "</b></font>", text)
                display_texts.append(text.strip()) # add the styled entry to the match list

    return dataset_matches, in_range_matches, display_texts


# User Interface
st.set_page_config(page_title="Corpora", layout="wide") # browser tab title and page layout; must be first st call
corpus_names = sorted( # determine corpus source options for the user based on filenames in DATA_FOLDER
    [f.replace(".tsv", "").replace("_", " ") for f in os.listdir(DATA_FOLDER) if f.endswith(".tsv")]
)
parameters, results, statistics = st.columns(spec=[0.2, 0.525, 0.275], gap="large") # columns with widths and gap size

# Search Parameters column
with parameters:
    st.markdown("#### Search Parameters")
    source = st.radio("**Source**:", corpus_names)
    query = st.text_input("**Search term**:").strip()
    st.caption("Use * as a wildcard and start with ^ to match at the start of a text")
    complexity_range = st.select_slider(
        label = "**Complexity range**:",
        options = [n/100 for n in range(0,101)],
        value=(0.0, 1.0),
        format_func = lambda x: x if x != 0 and x != 1.0 else ""
    )
    st.caption("*All benchmark data is sourced exclusively from training datasets*")
    # compile a corpus whenever a new radio button is selected
    corpus_data, corpus_vocab = compile_corpus(source)
    corpus_entry_count = len(corpus_data)
    corpus_vocab_size = len(corpus_vocab)
    corpus_token_count = sum(corpus_vocab.values())

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
        - Token count: {corpus_token_count:,}
        """
    )
    st.markdown("**Complexity Distribution** (hover to expand)")
    st.image(f"data/images/{source.replace(' ', '_')}_complexity.png")
    st.markdown("**Top Vocab**:")

    vocab_table = pd.DataFrame({ # convert string match data to table
        "word": corpus_vocab.keys(),
        "count": corpus_vocab.values(),
        "% in source": [round(100*(value/corpus_token_count), 2) or "<0.01" for value in corpus_vocab.values()]
    }).sort_values(by=["count", "word"], ascending=False).reset_index(drop=True)
    vocab_table.index += 1 # set row index to start from 1 instead of 0
    st.dataframe(vocab_table[:1000], use_container_width=True)

    if source.startswith("HotpotQA"):
        st.caption(HOTPOTQA_NOTICE)
    elif source == "Spoken English":
        st.caption(
            """
            The Spoken English source is a sample of the spoken portion of the British National Corpus and is offered as 
            a naturalistic point of comparison against written texts.
            """
        )

# execute a search when a query is given
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
                than one wildcard. If you just want a list of examples without a specific query, search for ^* (i.e. 
                all texts with a starting word). If you want a vocab list, check the 'Corpus Stats' tab under 
                'Statistics'.
                """
            )
    else:
        query = query.replace("*", "[\w\",'\-\<\+“”\.\\\\/:]+").replace(".", "\.") # convert text wildcard to RegEx
        query_re = re.compile(r"\b" + query + r"\b", flags=re.IGNORECASE) # compile query as RegEx
        dataset_matches, in_range_matches, entry_texts = find_matches(query_re, complexity_range, corpus_data) # extract search results
        match_count = sum(dataset_matches.values())
        in_range_match_count = sum(in_range_matches.values())

        # display results
        with results:       
            if not dataset_matches:
                st.markdown("There were no results for your search.")
            elif dataset_matches and not entry_texts:
                st.markdown("There were no results for your search in that complexity range.")
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
            if dataset_matches:
                st.markdown("**In whole dataset**")

                stats_table = pd.DataFrame({ # convert string match data to table
                    "match": dataset_matches.keys(),
                    "%": [str(round(100*(value/match_count), 2) or "<0.01") for value in dataset_matches.values()],
                    "entries": dataset_matches.values(),
                    "% of source": [
                        str(round(100*(value/corpus_entry_count), 2) or "<0.01") for value in dataset_matches.values()
                    ]
                }).sort_values(by=["entries", "match"], ascending=False).reset_index(drop=True)
                stats_table.index += 1 # set row index to start from 1 instead of 0
                st.dataframe(stats_table, use_container_width=True, hide_index=True)

                st.markdown(f"**In complexity range** ({complexity_range[0]}-{complexity_range[1]})")
                
                stats_table = pd.DataFrame({ # convert string match data to table
                    "match": in_range_matches.keys(),
                    "%": [
                        str(round(100*(value/in_range_match_count), 2) or "<0.01")
                        for value in in_range_matches.values()
                    ],
                    "entries": in_range_matches.values(),
                    "% of source": [str(round(100*(value/corpus_entry_count), 2) or "<0.01") for value in in_range_matches.values()]
                }).sort_values(by=["entries", "match"], ascending=False).reset_index(drop=True)
                stats_table.index += 1 # set row index to start from 1 instead of 0
                st.dataframe(stats_table, use_container_width=True, hide_index=True)

                if source == "HotpotQA Contexts":
                    st.caption("Each of the multiple contexts per HotpotQA question is counted as one entry.")
                if source.startswith("HotpotQA"):
                    st.caption(HOTPOTQA_NOTICE)
                if source == "Spoken English":
                    st.caption(
                        """
                        An ‘entry’ in the Spoken English source is roughly a turn in a conversation but this is 
                        situation-specific.
                        """
                    )
