from collections import defaultdict
import json

def import_json(filepath):
    """
    Load json data from filepath into a dict.
    """
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    return data

def import_benchmark_data(filepath, corpus_name, supporting_contexts_only=True):
    """
    Import NLU benchmark data from a JSON source into a list of dicts, where each dict encapsulates one test case.
    Each dict has the keys "questions" and "contexts", each with a list containing as many questions and/or contexts as
    come with the given test case.

    Illustration:
    [ # list of all benchmark test cases
        { # test case 1
            "questions":[QUESTION1, QUESTION2, ...], # question set for test case 1
            "contexts":[CONTEXT1, CONTEXT2, ...] # context set for test case 1
        },
        {...},
    ]
    """
    data = import_json(filepath)
    entries = []

    # DROP has the form:
    # [{"qa_pairs": [{"question": QUESTION}, ...], "passage": CONTEXT}, ...]
    if corpus_name == "drop":
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
    elif corpus_name == "hotpot":
        for test_case in data:
            if test_case["level"] != "hard": # only hard cases are tested by the benchmark
                continue
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
    elif corpus_name == "squad":
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
