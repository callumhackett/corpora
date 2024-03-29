import json
from collections import defaultdict

def import_benchmark_data(
        filepath, benchmark_name,
        include_keys=["title", "contexts", "questions"], hotpot_levels=["easy", "medium", "hard"],
        hotpot_distractors=True, return_as="cases"
    ):
    """
    Import benchmark data from a JSON file into a list of test cases or a dict of content types.

    The test case return is a list of dicts, where each dict has any of the keys "title", "contexts" and "questions" with lists of titles, contexts and questions per test case. The content type return is a dict with any of "titles", "contexts" and "questions", where each value is a list of all such content across all test cases.

    Args:
        filepath: the location of the benchmark JSON file
        benchmark_name: one of "drop", "hotpot", "squad2" for individualised processing
        include_keys: a list with any of "titles", "contexts", "questions" to specify what to import (default is all)
        hotpot_levels: a list with any of "easy", "medium", "hard" to filter by difficulty (default ["hard"])
        hotpot_distractors: a Boolean for whether to include the distractor contexts with hotpot (default False)
        return_as: one of "cases", "contents" to return either a list of test cases or a dict of content types (default "cases")
    """
    # load the data and initialise the imports
    with open(filepath, encoding="utf-8") as f:
        source = json.load(f)
    cases = []
    contents = defaultdict(list)

    if benchmark_name == "drop":
        # DROP has the form:
        # {ID:{"passage":CONTEXT, "qa_pairs":[{"question": QUESTION1}, {"question": QUESTION2}, ...]}, ...}
        for source_case in source.values():
            # define the data types
            source_data = {
                "contexts":[source_case["passage"].strip()],
                "questions":[qa_pair["question"].strip() for qa_pair in source_case["qa_pairs"]]
            }
            # return as specified
            if return_as == "cases":
                cases.append({key:source_data[key] for key in include_keys})
            elif return_as == "contents":
                for key in include_keys:
                    contents[key].extend(source_data[key])

    elif benchmark_name == "hotpot":
        # HotpotQA has the form:
        # [{"level": hard, "question": QUESTION, "context": [[SOURCE_NAME, [SENTENCE, SENTENCE, ...]], ...],
        #   "supporting_facts": [[SOURCE_NAME, FACT_LOCATION_INDEX], ...]}, ...]
        for source_case in source:
            # first filter by specified difficulty level
            if source_case["level"] not in hotpot_levels:
                continue
            # define the data types
            questions = [source_case["question"].strip()]
            if hotpot_distractors:
                contexts = [" ".join(context[1]) for context in source_case["context"]]
            else:
                supporting_titles = [context_details[0] for context_details in source_case["supporting_facts"]]
                contexts = [
                    " ".join(context[1]) for context in source_case["context"] if context[0] in supporting_titles
                ]
            source_data = {"questions":questions, "contexts":contexts}
            # return as specified
            if return_as == "cases":
                cases.append({key:source_data[key] for key in include_keys})
            elif return_as == "contents":
                for key in include_keys:
                    contents[key].extend(source_data[key])

    elif benchmark_name == "squad2":
        # SQuAD2.0 has the form:
        # {"data": [{"paragraphs": [{"qas": [{"question": QUESTION}, ...], "context": CONTEXT}, ...]}, ...]}
        source = source["data"]
        for grouping in source:
            for source_case in grouping["paragraphs"]:
                # define the data types
                source_data = {
                    "title":[grouping["title"]],
                    "contexts":[source_case["context"].strip()],
                    "questions":[qa_pair["question"].strip() for qa_pair in source_case["qas"]]
                }
                # return as specified
                if return_as == "cases":
                    cases.append({key:source_data[key] for key in include_keys})
                elif return_as == "contents":
                    for key in include_keys:
                        contents[key].extend(source_data[key])
    
    if return_as == "cases":
        return cases
    
    return contents
