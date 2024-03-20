import json

def import_benchmark_data(
        filepath, benchmark_name,
        inclusions=["titles", "contexts", "questions"], hotpot_levels=["hard"], hotpot_distractors=False
    ):
    """
    Import benchmark data from a JSON file into a list of dicts, where each dict encapsulates one test case.
    
    Each dict may have any of the keys "title", "contexts" and "questions", where "title" is a string describing the topic and "contexts" and "questions" are lists having as many items as there are contexts and questions per test case.

    Args:
        filepath: the location of the JSON file
        benchmark_name: one of "drop", "hotpot", "squad", for individualised processing
        inclusions: a list with any combination of "titles", "contexts", "questions" (default includes all)
        hotpot_levels: a list with any combination of "easy", "medium", "hard" to filter by difficulty (default ["hard"])
        hotpot_distractors: a Boolean determining whether to include the distracting contexts with hotpot (default False)
    """
    # import the data and initialise the extraction
    with open(filepath, encoding="utf-8") as f:
        source = json.load(f)
    data = []

    if benchmark_name == "drop":
        # DROP has the form:
        # {ID:{"passage":CONTEXT, "qa_pairs":[{"question": QUESTION1}, {"question": QUESTION2}, ...]}, ...}
        for test_case in source.values():
            extraction = {}
            if "contexts" in inclusions:
                extraction["contexts"] = [test_case["passage"].strip()]
            if "questions" in inclusions:
                extraction["questions"] = [qa_pair["question"].strip() for qa_pair in test_case["qa_pairs"]]
            data.append(extraction)

    elif benchmark_name == "hotpot":
        # HotpotQA has the form:
        # [{"level": hard, "question": QUESTION, "context": [[SOURCE_NAME, [SENTENCE, SENTENCE, ...]], ...],
        #   "supporting_facts": [[SOURCE_NAME, FACT_LOCATION_INDEX], ...]}, ...]
        for test_case in source:
            # filter by difficulty level
            if test_case["level"] not in hotpot_levels:
                continue
            extraction = {}
            if "contexts" in inclusions:
                # add distractors
                if hotpot_distractors:
                    extraction["contexts"] = [" ".join(context[1]) for context in test_case["context"]]
                # or exclude them
                else:
                    supporting_titles = [context_details[0] for context_details in test_case["supporting_facts"]]
                    extraction["contexts"] = [
                        " ".join(context[1]) for context in test_case["context"] if context[0] in supporting_titles
                    ]
            if "questions" in inclusions:
                extraction["questions"] = [test_case["question"].strip()]
            data.append(extraction)

    elif benchmark_name == "squad":
        # SQuAD2.0 has the form:
        # {"data": [{"paragraphs": [{"qas": [{"question": QUESTION}, ...], "context": CONTEXT}, ...]}, ...]}
        source = source["data"]
        for grouping in source:
            for test_case in grouping["paragraphs"]:
                extraction = {}
                if "titles" in inclusions:
                    extraction["title"] = grouping["title"]
                if "contexts" in inclusions:
                    extraction["contexts"] = [test_case["context"].strip()]
                if "questions" in inclusions:
                    extraction["questions"] = [qa_pair["question"].strip() for qa_pair in test_case["qas"]]
                data.append(extraction)

    return data
