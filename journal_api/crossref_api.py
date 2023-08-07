"""
crossref_api
"""
import requests
import pandas as pd
import numpy as np
import json
import yaml
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
    if data != "" and len(data) > 0:
        for author in data:
            author = " ".join([author.get("given", ""), author.get("family","")])
            ret.append(author)
    else:
        print("WARN: No authors!")
    return ret

def _remake_references(data):
    ret = []
    if data != "" and len(data) > 0:
        for ref in data:
            if ref.get("article-title", "") != "":
                ret.append(ref["article-title"])
            elif ref.get("DOI", "") != "":
                ret.append(search_title_by_doi(ref["DOI"]))
            else:
                print("WARN: No information of reference", ref)
    else:
        print("WARN: No reference!")
    return ret


def search(title):
    """
    search
    """
    title_rm = _remove_punctuation(title)
    url = "https://api.crossref.org/works"

    params = {
        "query.title": title_rm,
        "rows": 1  # Number of results to retrieve
    }

    # Send the API request
    if settings["USE_PROXY"] == True:
        response = requests.get(url, params=params, proxies=proxies, timeout=15)
    else:
        response = requests.get(url, params=params, timeout=15)

    # Parse the JSON response
    data = response.json()

    # Extract the relevant information from the response
    if data.get("status", "") != "" and data["status"] == "ok":
        papers = data["message"]["items"]
        if len(papers) > 0:
            paper = papers[0]
            # Access the paper information
            if(paper.get("title", "") != "" and len(paper["title"]) > 0):
                title_f = paper["title"][0]
                if fuzz.token_set_ratio(title.lower(), title_f.lower()) == 100:  # check if the result is same with the query
                    new_paper = {}
                    new_paper["title"] = title_f
                    new_paper["abstract"] = paper.get("abstract", "")
                    new_paper["tldr"] = ""
                    new_paper["fieldOfStudy"] = paper.get("subject", [])
                    new_paper["authors"] = _remake_authors(paper.get("author",""))
                    new_paper["references"] = _remake_references(paper.get("reference",""))
                    return new_paper
                else:
                    print("WARN: Found! Title doesn't matched. Title:", title, ", Found:", title_f)
            else:
                print("ERROR: Not found")
    return None


def similar_search(title, rows):
    """
    crossref_search
    """
    # Specify the API endpoint
    ENDPOINT = "https://api.crossref.org/works"

    # Set up the query parameters
    params = {
        "query.title": title,
        "rows": rows  # Number of results to retrieve
    }

    # Send the API request
    response = requests.get(ENDPOINT, params=params, timeout=10)

    # Parse the JSON response
    data = response.json()

    paper_list = []
    # Extract the relevant information from the response
    if data["status"] == "ok":
        papers = data["message"]["items"]
        if len(papers) > 0:
            for paper in papers:
                if(paper.get("title", "") != "" and len(paper["title"]) > 0):
                    paper_list.append(paper["title"][0])
                else:
                    print("ERROR: Not found")
    return paper_list
            

def reference_doi_list(data):
    return "go"


def search_title_by_doi(doi):
    base_url = "https://api.crossref.org/works/"
    url = base_url + doi

    data = ""
    if settings["USE_PROXY"] == True:
        response = requests.get(url, proxies=proxies, timeout=10)
    else:
        response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()

    # Extract the relevant information from the response
    if data.get("status", "") != "" and data["status"] == "ok":
        paper = data["message"]
        
        # Access the paper information
        if(paper.get("title", "") != "" and len(paper["title"]) > 0):
            title = paper["title"][0]
            return title
        else:
            print("ERROR: Not found")
    return ""


def similar_search(title, rows):
    """
    crossref_search
    """
    # Specify the API endpoint
    ENDPOINT = "https://api.crossref.org/works"

    # Set up the query parameters
    params = {
        "query.title": title,
        "rows": rows  # Number of results to retrieve
    }

    # Send the API request
    response = requests.get(ENDPOINT, params=params, timeout=10)

    # Parse the JSON response
    data = response.json()

    paper_list = []
    # Extract the relevant information from the response
    if data["status"] == "ok":
        papers = data["message"]["items"]
        if len(papers) > 0:
            for paper in papers:
                paper_list.append(paper["title"][0])
    return paper_list


def extract_authors_references(data):
    if (data != "" or data != None):
        authors = []
        references = pd.DataFrame(columns=["doi", "title", "crossref"])
        # get the authors
        if data.get("author", "") != "":
            for author in data["author"]:
                author = " ".join([author.get("given", ""), author.get("family","")])
                authors.append(author)

        # get the references
        if data["reference-count"] > 0:
            for ref in data["reference"]:
                references = references.append({"doi": ref.get("DOI", ""), "title": ref.get("article-title", ""), "crossref": False if ref.get("DOI", "") == "" else True}, ignore_index=True)
    
        return authors, references
    return None, None


def generate_title_auths_refs(df):
    df["authors"] = np.full(len(df), "").tolist()
    df["refs"] = np.full(len(df), "").tolist()
    for index, ref in df.iterrows():
        if ref["doi"] == "":
            cs = search(ref["title"])
            if cs != "":
                df.loc[index, "crossref"] = True
                df.loc[index, "doi"] = cs["DOI"]
        else:
            cs = search_by_doi(ref["doi"])
            if(cs.get("title", "") != "" and len(cs["title"]) > 0):
                df.loc[index, "title"] = cs["title"][0]
            else:
                print("ERROR: Can't find title.")
        # break
        if cs != "":
            # print("json:", json.dumps(cs))
            ref_auths, ref_refs = extract_authors_references(cs)
            df.loc[index, "authors"] = ref_auths
            df.loc[index, "refs"] = ref_refs.to_json()
    return df     