"""
googlebook_api
"""

import yaml
import requests
from requests.exceptions import ReadTimeout
import logging
import logging.config
import string
from thefuzz import fuzz

with open("settings.yaml") as yaml_file:
    settings = yaml.safe_load(yaml_file)

with open('logging_config.yaml', 'r') as config_file:
    log_config = yaml.safe_load(config_file)

proxies = {
    'http': settings["HTTP_PROXY"],
    'https': settings["HTTPS_PROXY"],
}

timeout = settings["REQUEST_TIMEOUT"]
logging.config.dictConfig(log_config)



def _remove_punctuation(text):
    translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    return text.translate(translator)

def search(title, start_year = 2010):
    """
    search
    """
    title_rm = _remove_punctuation(title)

    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": f"intitle:{title_rm}",
        "maxResults": 1,  # Number of results to retrieve
        "key": settings["GOOGLEBOOK_API"]  # Replace with your actual API key
    }

    data = ""
    try:
        if settings["USE_PROXY"] == True:
            response = requests.get(url, params=params, proxies=proxies, timeout=timeout)
        else:
            response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()

        if response.status_code == 200:
            data = response.json()
    except ReadTimeout:
        logging.error(f"gb.search: Request timed out.")
    except requests.RequestException as e:
        logging.error(f"gb.search: An error occurred: {e}")

    # Process the response data
    if "items" in data:
        for item in data["items"]:
            volume_info = item["volumeInfo"]
            book_title = volume_info["title"]
            book_subtitle = volume_info.get("subtitle", "")
            authors = volume_info.get("authors", [])
            description = volume_info.get("description", "")
            categories = volume_info.get("categories", [])
            pubdate = volume_info.get("publishedDate", "")

            rt = book_title + " " + book_subtitle
            if fuzz.token_sort_ratio(title.lower(), rt.lower()) > 95:
                logging.debug(f"gb.search:  Matched! title={rt}")
                ret = {}
                ret["title"] = rt
                ret["abstract"] = description
                ret["tldr"] = ""
                ret["year"] = int(pubdate[:4]) if len(pubdate) > 3 else ""
                ret["fieldsOfStudy"] = categories
                ret["authors"] = [str(i) for i in authors]
                ret["references"] = []
                ret["citationCount"] = -1
                ret["influentialCitationCount"] = -1
                ret["source"] = "gbook"
                return ret
            else:
                logging.debug(f"gb.search: Found! Title doesn't match! title={title}, result={rt}")
                return None
    logging.debug(f"gb.search: Not found! title={title}")
    return None