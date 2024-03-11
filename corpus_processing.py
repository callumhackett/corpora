from collections import defaultdict
import json
import random
import os
import xml.etree.ElementTree as ET

def all_files_in(filepath):
    """
    Return a list of alphabetically sorted filepaths for all files in a folder and its subfolders.
    """
    files = []
    for path, _, filenames in os.walk(filepath):
        for name in filenames:
            files.append(os.path.join(path, name))

    return sorted(files)

def load_json(filepath):
    """
    Load json data into a dict.
    """
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    return data

def import_benchmark_data(filepath, corpus, supporting_contexts_only=True):
    """
    Import NLU benchmark data into a list of dicts, where each dict contains the keys "questions" and "contexts", with 
    each of these having a list of the questions or contexts that pertain to one test case in the benchmark.
    """
    data = load_json(filepath)
    entries = []

    # DROP has the form:
    # [{"qa_pairs": [{"question": QUESTION}, ...], "passage": CONTEXT}, ...]
    if corpus == "DROP":
        for test_case in data.values():
            entry = defaultdict(list)
            # add the questions (multiple)
            for qa_pair in test_case["qa_pairs"]:
                question = qa_pair["question"].strip()
                entry["questions"].append(question)
            # add the context (single)
            context = test_case["passage"].strip()
            entry["contexts"].append(context)
            entries.append(entry)
    
    # HotpotQA has the form:
    # [{"level": hard, "question": QUESTION, "context": [[SOURCE_NAME, [SENTENCE, SENTENCE, ...]], ...],
    #   "supporting_facts": [[SOURCE_NAME, FACT_LOCATION], ...]}, ...]
    elif corpus == "HotpotQA":
        for test_case in data:
            if test_case["level"] != "hard":
                pass
            entry = defaultdict(list)
            # add the question (single)
            question = test_case["question"].strip()
            entry["questions"].append(question)
            # add the contexts (multiple)
            named_contexts = test_case["context"]
            supporting_context_names = [context_details[0] for context_details in test_case["supporting_facts"]]
            for context in named_contexts:
                context_name = context[0]
                context_content = " ".join(context[1]).strip().replace("\n", " ")
                if supporting_contexts_only:
                    if context_name in supporting_context_names:
                        entry["contexts"].append(context_content)
                else:
                    entry["contexts"].append(context_content)
            entries.append(entry)

    # SQuAD2.0 has the form:
    # {"data": [{"paragraphs": [{"qas": [{"question": QUESTION}, ...], "context": CONTEXT}, ...]}, ...]}
    elif corpus == "SQuAD2.0":
        data = data["data"]
        for topic in data:
            test_cases = topic["paragraphs"]
            for test_case in test_cases:
                entry = defaultdict(list)
                # add the questions (multiple)
                qa_pairs = test_case["qas"]
                for qa_pair in qa_pairs:
                    question = qa_pair["question"].strip()
                    entry["questions"].append(question)
                # add the context (single)
                context = test_case["context"].strip()
                entry["contexts"].append(context)
                entries.append(entry)

    return entries

def write_benchmark_data(filepath, corpus):
    """Write benchmark data to file with contexts followed by their associated questions."""
    with open(filepath, mode="w", encoding="utf-8") as f:
        for entry in corpus:
            for context in entry["contexts"]:
                f.write(context+"\n")
            for question in entry["questions"]:
                f.write(question+"\n")
            f.write("\n")

def xml_to_string(filepath):
    """Extract the text from an XML file."""
    content = ET.parse(filepath)
    root = content.getroot()
    text = str(ET.tostring(root, encoding="unicode", method="text"))

    return text
