import json
from collections import defaultdict

def import_benchmark_data(
        filepath, benchmark_name,
        inclusions=["titles", "contexts", "questions"], organise_by="cases",
        hotpot_levels=["hard"], hotpot_distractors=False
    ):
    """
    Import benchmark data from a JSON file into a list of test cases (each a dict) or a dict of content types (each a list).

    The test case return is a list of dicts, where each dict can have the keys "title", "contexts" and "questions" with lists of titles, contexts and questions per test case. The content type return is a dict with any of "titles", "contexts" and "questions", where each value is a list of all such content across all test cases.

    Args:
        filepath: the location of the JSON file
        benchmark_name: one of "drop", "hotpot", "squad2" for individualised processing
        inclusions: a list with any of "titles", "contexts", "questions" (default is all)
        organise_by: one of "cases", "content" to return either a list of test cases or a dict of content types (default "cases")
        hotpot_levels: a list with any of "easy", "medium", "hard" to filter by difficulty (default ["hard"])
        hotpot_distractors: a Boolean for whether to include the distractor contexts with hotpot (default False)
    """
    # import the data and initialise the extraction
    with open(filepath, encoding="utf-8") as f:
        source = json.load(f)
    cases = []
    contents = defaultdict(list)

    if benchmark_name == "drop":
        # DROP has the form:
        # {ID:{"passage":CONTEXT, "qa_pairs":[{"question": QUESTION1}, {"question": QUESTION2}, ...]}, ...}
        for source_case in source.values():
            source_data = {
                "contexts":[source_case["passage"].strip()],
                "questions":[qa_pair["question"].strip() for qa_pair in source_case["qa_pairs"]]
            }
            if organise_by == "cases":
                cases.append({inclusion:source_data[inclusion] for inclusion in inclusions})
            elif organise_by == "content":
                for inclusion in inclusions:
                    contents[inclusion].extend(source_data[inclusion])

    elif benchmark_name == "hotpot":
        # HotpotQA has the form:
        # [{"level": hard, "question": QUESTION, "context": [[SOURCE_NAME, [SENTENCE, SENTENCE, ...]], ...],
        #   "supporting_facts": [[SOURCE_NAME, FACT_LOCATION_INDEX], ...]}, ...]
        for source_case in source:
            if source_case["level"] not in hotpot_levels:
                continue
            source_data = {"questions":[source_case["question"].strip()]}
            if hotpot_distractors:
                source_data["contexts"] = [" ".join(context[1]) for context in source_case["context"]]
            else:
                supporting_titles = [context_details[0] for context_details in source_case["supporting_facts"]]
                source_data["contexts"] = [
                    " ".join(context[1]) for context in source_case["context"] if context[0] in supporting_titles
                ]
            if organise_by == "cases":
                cases.append({inclusion:source_data[inclusion] for inclusion in inclusions})
            elif organise_by == "content":
                for inclusion in inclusions:
                    contents[inclusion].extend(source_data[inclusion])

    elif benchmark_name == "squad2":
        # SQuAD2.0 has the form:
        # {"data": [{"paragraphs": [{"qas": [{"question": QUESTION}, ...], "context": CONTEXT}, ...]}, ...]}
        source = source["data"]
        for grouping in source:
            for source_case in grouping["paragraphs"]:
                source_data = {
                    "titles":[grouping["title"]],
                    "contexts":[source_case["context"].strip()],
                    "questions":[qa_pair["question"].strip() for qa_pair in source_case["qas"]]
                }
                if organise_by == "cases":
                    cases.append({inclusion:source_data[inclusion] for inclusion in inclusions})
                elif organise_by == "content":
                    for inclusion in inclusions:
                        contents[inclusion].extend(source_data[inclusion])
    
    if organise_by == "cases":
        return cases
    
    return contents
