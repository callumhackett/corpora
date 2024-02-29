from collections import Counter
import json
import re
import pandas as pd
import streamlit as st

st.markdown("### Corpus Search")

# to do: change sources and present them as something other than dropdown list
# to do: have associated choice for max number of results per source
sources = st.multiselect("Data sources:", ["HotpotQA Questions", "HotpotQA Contexts"])

with open("data/hotpot_train_v1.1_questions.txt", encoding="utf-8") as data:
    questions = [line.rstrip() for line in data]

num_questions = len(questions)

case_sensitive = st.toggle('Case sensitive')
case_flag = re.IGNORECASE if not case_sensitive else 0

query = st.text_input('Search term: ').strip().replace("*", "\w+")
query_re = re.compile(r"\b" + query + r"\b", flags=case_flag)

if query:
    if "Questions" in sources:

        matches = []
        match_count = 0

        # Find the matches
        for q in questions:
            match = re.findall(query_re, q)
            if query != "" and match:
                match_count += len(match)
                matches.append((match, q))

        # Get some stats
        text_hits, _ = zip(*matches)
        all_hits = [x for xs in text_hits for x in xs]
        if not case_sensitive:
            all_hits = [t.lower() for t in all_hits]
        hit_counts = Counter(all_hits)
        num_unique_hits = len(hit_counts)
        hit_df = pd.DataFrame(
            {"Hit": hit_counts.keys(), "Count": hit_counts.values()}
        ).sort_values(by=["Count", "Hit"], ascending=False).reset_index(drop=True)

        st.markdown(f"Unique hits: {len(hit_df)}")
        st.dataframe(hit_df, column_config={"Hit": st.column_config.TextColumn()})
        st.dataframe(hit_df["Count"].describe().to_frame().transpose()[["mean", "std", "min", "max"]])

        # Underscore the hits
        st.markdown(f"### Questions Results ({match_count})")
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

    if "Contexts" in sources:

        st.write("Context data not ready yet")