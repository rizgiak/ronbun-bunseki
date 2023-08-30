"""
arxiv_api
"""

import yaml
import arxiv
import string
from thefuzz import fuzz
import logging
import logging.config

with open("logging_config.yaml", "r") as config_file:
    log_config = yaml.safe_load(config_file)

logging.config.dictConfig(log_config)


def _remove_punctuation(text):
    translator = str.maketrans(string.punctuation, " " * len(string.punctuation))
    return text.translate(translator)


def search(title, start_year=2010):
    title_rm = _remove_punctuation(title)

    try:
        search = arxiv.Search(
            query=title_rm, max_results=1, sort_by=arxiv.SortCriterion.Relevance
        )
    except Exception as e:
        logging.error(f"ax.search: An error occurred: title={title}, msg={e}")
        return None

    for result in search.results():
        if fuzz.token_sort_ratio(title.lower(), result.title.lower()) > 95:
            logging.debug(f"ax.search:  Matched! title={title}")

            ret = {}
            ret["title"] = result.title
            ret["abstract"] = result.summary
            ret["tldr"] = ""
            ret["year"] = int(str(result.published)[:4]) if len(str(result.published)) > 3 else ""
            ret["fieldsOfStudy"] = result.categories
            ret["authors"] = [str(i) for i in result.authors]
            ret["references"] = []
            ret["citationCount"] = -1
            ret["influentialCitationCount"] = -1
            ret["source"] = "arxiv"
            return ret
        else:
            logging.debug(f"ax.search: Found! Title doesn't match! title={title}, result={result.title}")
            return None
    logging.debug(f"ax.search: Not found! title={title}")
    return None