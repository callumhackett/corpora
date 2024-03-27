import json

def import_benchmark_data(
        filepath, benchmark_name,
        inclusions=["titles", "contexts", "questions"], organise_by="cases",
        hotpot_levels=["hard"], hotpot_distractors=False
    ):
    """
    Import benchmark data from a JSON file into a list of test cases (each a dict) or a dict of content types (each a list).

    The test case return gives a list of dicts, where each dict can have any of the keys "title", "contexts" and "questions" with lists of titles, contexts and questions per test case. The content type return gives a dict of "titles", "contexts" and "questions", where each has a list for all such content across all test cases.

    Args:
        filepath: the location of the JSON file
        benchmark_name: one of "drop", "hotpot", "squad2" for individualised processing
        inclusions: a list with any combination of "titles", "contexts", "questions" (default lists all)
        organise_by: one of "cases", "content" to return either a list of test cases or a dict of content types (default "cases")
        hotpot_levels: a list with any of "easy", "medium", "hard" to filter by difficulty (default ["hard"])
        hotpot_distractors: a Boolean for whether to include the distractor contexts with hotpot (default False)
    """
    # import the data and initialise the extraction
    with open(filepath, encoding="utf-8") as f:
        source = json.load(f)
    case_data = []

    if benchmark_name == "drop":
        # DROP has the form:
        # {ID:{"passage":CONTEXT, "qa_pairs":[{"question": QUESTION1}, {"question": QUESTION2}, ...]}, ...}
        for test_case in source.values():
            extraction = {}
            if "contexts" in inclusions:
                extraction["contexts"] = [test_case["passage"].strip()]
            if "questions" in inclusions:
                extraction["questions"] = [qa_pair["question"].strip() for qa_pair in test_case["qa_pairs"]]
            case_data.append(extraction)

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
            case_data.append(extraction)

    elif benchmark_name == "squad2":
        # SQuAD2.0 has the form:
        # {"data": [{"paragraphs": [{"qas": [{"question": QUESTION}, ...], "context": CONTEXT}, ...]}, ...]}
        source = source["data"]
        for grouping in source:
            for test_case in grouping["paragraphs"]:
                extraction = {}
                if "titles" in inclusions:
                    extraction["titles"] = grouping["title"]
                if "contexts" in inclusions:
                    extraction["contexts"] = [test_case["context"].strip()]
                if "questions" in inclusions:
                    extraction["questions"] = [qa_pair["question"].strip() for qa_pair in test_case["qas"]]
                case_data.append(extraction)

    if organise_by == "content":
        content_data = {inclusion:[] for inclusion in inclusions}
        for test_case in case_data:
            for label, content in test_case.items():
                content_data[label].extend(content)
        return content_data

    return case_data
