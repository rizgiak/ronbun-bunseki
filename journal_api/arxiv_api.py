"""
arxiv_api
"""

import yaml
import arxiv
import string
from thefuzz import fuzz
import logging

with open("logging_config.yaml", "r") as config_file:
    log_config = yaml.safe_load(config_file)

logging.config.dictConfig(log_config)


def _remove_punctuation(text):
    translator = str.maketrans(string.punctuation, " " * len(string.punctuation))
    return text.translate(translator)


def search(title, start_year=2010):
    title_rm = _remove_punctuation(title)

    search = arxiv.Search(
        query=title_rm, max_results=1, sort_by=arxiv.SortCriterion.Relevance
    )

    for result in search.results():
        if fuzz.token_set_ratio(title.lower(), result.title.lower()) == 100:
            logging.debug(f"ax.search:  Matched! title={title}")
            year = int(str(result.published)[:4]) if len(str(result.published)) > 3 else ""
            if year != "" and year < start_year:
                logging.debug(f"ax.search: Unmatched. year={year}, start_year={start_year}")
                return None
            ret = {}
            ret["title"] = result.title
            ret["abstract"] = result.summary
            ret["tldr"] = ""
            ret["year"] = year
            ret["fieldsOfStudy"] = result.categories
            ret["authors"] = [str(i) for i in result.authors]
            ret["references"] = []
            ret["source"] = "arxiv"
            return ret
    return None