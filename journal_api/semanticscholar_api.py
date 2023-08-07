"""
semanitcsholar_api
"""

import yaml
import requests
import string
from thefuzz import fuzz

with open("settings.yaml") as yaml_file:
    settings = yaml.safe_load(yaml_file)

proxies = {
    'http': settings["HTTP_PROXY"],
    'https': settings["HTTPS_PROXY"],
}

def _remove_punctuation(text):
    translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    return text.translate(translator)

def _remake_authors(data):
    ret = []
    if len(data) > 0:
        for i in data:
            ret.append(i["name"])
    else:
        print("WARN: No authors!")
    return ret

def _remake_references(data):
    ret = []
    if len(data) > 0:
        for i in data:
            ret.append(i["title"])
    else:
        print("WARN: No references!")
    return ret

def _remake_tldr(data):
    ret = ""
    if data.get("text", "") != "":
        ret = data["text"]
    else:
        print("WARN: No tldr!")
    return ret

def search(title):
    title_rm = _remove_punctuation(title)
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    headers = {'x-api-key': settings["SS_API"]}
    params={'query': title_rm, 'limit': 1, 'fields': 'title,abstract,tldr,fieldsOfStudy,authors,references'}

    if settings["USE_PROXY"] == True:
        response = requests.get(url, headers=headers, params=params, proxies=proxies, timeout=10)
    else:
        response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    # Process the response data
    if data.get("total", "") != "" and data["total"] > 0:
        paper = data["data"][0]
        # Access the paper information
        if(paper.get("title", "") != ""):
            title_f = paper["title"]
            if fuzz.token_set_ratio(title.lower(), title_f.lower()) == 100:  # check if the result is same with the query
                paper["tldr"] = _remake_tldr(paper["tldr"])
                paper["authors"] = _remake_authors(paper["authors"])
                paper["references"] = _remake_references(paper["references"])
                return paper
            else:
                print("WARN: Found! Title doesn't matched. Title:", title, ", Found:", title_f)
        else:
            print("ERROR: Not found")
    return None