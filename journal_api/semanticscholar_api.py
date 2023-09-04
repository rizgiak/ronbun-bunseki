"""
semanitcsholar_api
"""

import yaml
import requests
from requests.exceptions import ReadTimeout
import logging
import logging.config
import string
import time
from thefuzz import fuzz

sleep_duration = 0.0625  # to limit query based on ss API reuqirements to avoid Error 426. 1/16 (5000 query in 5 minutes)

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

def _remake_authors(data):
    ret = []
    if len(data) > 0:
        for i in data:
            ret.append(i["name"])
    else:
        logging.warn(f"ss._remake_authors: No authors!")
    return ret

def _remake_references(data, year, skip_unknown_year):
    year_flag = False
    ret = []
    if len(data) > 0:
        for i in data:
            y = i.get("year", "")
            if y != "" and y != None:
                year_flag = True
                if int(y) >= year:
                    ret.append(i["title"])
            else:
                logging.warn(f"ss._remake_references: Unknown year. skip_unknown_year={skip_unknown_year}, title={i['title']}")
                if not skip_unknown_year:
                    ret.append(i["title"])
    else:
        logging.warn(f"ss._remake_references: No references!")
    
    # if all references below year
    if year_flag and len(ret) == 0:
        logging.warn(f"ss._remake_references: All references below start year!")
        ret = -1

    return ret

def _remake_tldr(data):
    ret = ""
    if data != None and data != "" and data.get("text", "") != "":
        ret = data["text"]
    else:
        logging.warn(f"ss._remake_tldr: No tldr!")
    return ret

def _remake_year(data):
    if data == None:
        data = ""
    return data

def search(title, start_year = 2010, filter_year_for_all = False, skip_unknown_year = False):
    """
    search\n
    Parameters:\n
    title = title of the paper\n
    start_year = starting year to search\n
    filter_year_for_all = Activate filter year so if year below the start_year result will be None\n
    skip_unknown_year = if the year of the references are '' or unknown, [True] will skip the reference
    """
    title_rm = _remove_punctuation(title)
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    headers = {'x-api-key': settings["SS_API"]}
    params={'query': title_rm, 'limit': 1, 'fields': 'title,abstract,tldr,fieldsOfStudy,year,authors,references.title,references.year,citationCount,influentialCitationCount'}

    data = ""
    try:
        time.sleep(sleep_duration)
        if settings["USE_PROXY"] == True:
            response = requests.get(url, headers=headers, params=params, proxies=proxies, timeout=timeout)
        else:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()

        if response.status_code == 200:
            data = response.json()
    except ReadTimeout:
        logging.error(f"ss.search: Request timed out.")
    except requests.RequestException as e:
        logging.error(f"ss.search: An error occurred: {e}")


    # Process the response data
    if data != "" and data.get("total", "") != "" and data["total"] > 0:
        paper = data["data"][0]
        # Access the paper information
        if(paper.get("title", "") != ""):
            title_f = paper["title"]
            if fuzz.token_sort_ratio(title.lower(), title_f.lower()) > 95:  # check if the result is same with the query
                logging.debug(f"ss.search: Found! title={title_f}")
                # REDUNDANT
                if filter_year_for_all:
                    if paper.get("year", "") != ""  and paper["year"] != None and paper["year"] < start_year:
                        logging.debug(f"ss.search: Unmatched. year={paper['year']}, start_year={start_year}")
                        return None
                paper["year"] = _remake_year(paper["year"])
                paper["tldr"] = _remake_tldr(paper.get("tldr", ""))
                paper["authors"] = _remake_authors(paper.get("authors", []))
                paper["references"] = _remake_references(paper["references"], start_year, skip_unknown_year)
                paper["source"] = "semanticscholar"
                return paper
            else:
                logging.debug(f"ss.search: Found! Title doesn't match! title={title}, result={title_f}")
        else:
            logging.debug(f"ss.search: Not found! title={title}")
    return None