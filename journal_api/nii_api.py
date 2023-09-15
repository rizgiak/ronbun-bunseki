"""
nii_api
"""

import requests
from rdflib import Graph, Namespace
from requests.exceptions import ReadTimeout
import logging
import logging.config
import string
import yaml
from thefuzz import fuzz

with open("settings.yaml") as yaml_file:
    settings = yaml.safe_load(yaml_file)

with open("logging_config.yaml", "r") as config_file:
    log_config = yaml.safe_load(config_file)

proxies = {
    "http": settings["HTTP_PROXY"],
    "https": settings["HTTPS_PROXY"],
}

timeout = settings["REQUEST_TIMEOUT"]
logging.config.dictConfig(log_config)

# Define namespaces
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
ns = Namespace("http://purl.org/rss/1.0/")
dc = Namespace("http://purl.org/dc/elements/1.1/")
opensearch = Namespace("http://a9.com/-/spec/opensearch/1.1/")
prism = Namespace("http://prismstandard.org/namespaces/basic/2.0/")


def _remove_punctuation(text):
    translator = str.maketrans(string.punctuation, " " * len(string.punctuation))
    return text.translate(translator)


def _remake_year(year):
    ryear = str(year)
    if len(ryear) >= 4:
        ryear = int(ryear[:4])
    else:
        ryear = ""
    return ryear

def search(title, lang="jp"):
    """
    search\n
    Parameters:\n
    title = title of the paper\n
    lang = Either 'jp' or 'eng'\n
    """
    title_rm = _remove_punctuation(title)
    url = "https://cir.nii.ac.jp/opensearch/articles"
    params = {"q": title_rm, "count": 1, "lang": lang, "format": "rss"}

    data = ""
    try:
        # Send the API request
        if settings["USE_PROXY"] == True:
            response = requests.get(
                url, params=params, proxies=proxies, timeout=timeout
            )
        else:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()

        if response.status_code == 200:
            data = response.content
    except ReadTimeout:
        logging.error(f"cr.search: Request timed out. title={title}")
    except requests.RequestException as e:
        logging.error(f"cr.search: An error occurred: {e}, title={title}")

    if data != "":
        # Parse the RDF/XML data
        g = Graph()
        g.parse(data=data, format="xml")

        # Extract information
        # channel = next(g.subjects(predicate=ns.type, object=ns.RDFBag), None)
        # title = next(g.objects(subject=channel, predicate=ns.title), None)
        item = next(g.subjects(predicate=RDF.type, object=ns.item), None)
        item_title = next(g.objects(subject=item, predicate=ns.title), None)
        item_link = next(g.objects(subject=item, predicate=ns.link), None)
        creators = list(g.objects(subject=item, predicate=dc.creator))
        item_description = next(g.objects(subject=item, predicate=ns.description), None)
        subjects = list(g.objects(subject=item, predicate=dc.subject))
        year = next(g.objects(subject=item, predicate=prism.publicationDate), None)
        if fuzz.token_sort_ratio(title.lower(), str(item_title).lower()) > 95:
            new_paper = {}
            new_paper["title"] = str(item_title)
            new_paper["abstract"] = str(item_description)
            new_paper["tldr"] = ""
            new_paper["year"] = _remake_year(year)
            new_paper["fieldsOfStudy"] = []
            new_paper["authors"] = [str(creator) for creator in creators]
            new_paper["references"] = []
            new_paper["citationCount"] = -1
            new_paper["influentialCitationCount"] = -1
            new_paper["source"] = "nii"
            keywords = [str(subject) for subject in subjects]
            return new_paper
        else:
            logging.debug(
                f"nii.search: Found! Title doesn't match! title={title}, result={item_title}"
            )
            return None
    
    logging.debug(f"nii.search: Not found! title={title}")
    return None
