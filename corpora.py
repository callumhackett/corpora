import streamlit as st

with open("corpus.txt") as f:
    text = f.read()

st.write(text)