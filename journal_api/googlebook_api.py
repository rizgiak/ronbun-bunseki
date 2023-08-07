"""
googlebook_api
"""

import yaml
import requests
import string
from thefuzz import fuzz

with open("settings.yaml") as yaml_file:
    settings = yaml.safe_load(yaml_file)

def _remove_punctuation(text):
    translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    return text.translate(translator)

def search(title):
    
    title_rm = _remove_punctuation(title)

    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": f"intitle:{title_rm}",
        "maxResults": 1,  # Number of results to retrieve
        "key": settings["GOOGLEBOOK_API"]  # Replace with your actual API key
    }

    response = requests.get(url, params=params)
    data = response.json()
    # print(json.dumps(data))
    # Process the response data
    if "items" in data:
        for item in data["items"]:
            volume_info = item["volumeInfo"]
            book_title = volume_info["title"]
            book_subtitle = volume_info.get("subtitle", "")
            authors = volume_info.get("authors", [])
            description = volume_info.get("description", "")
            categories = volume_info.get("categories", [])

            rt = book_title + " " + book_subtitle
            if fuzz.token_set_ratio(title.lower(), rt.lower()) > 95:
                ret = {}
                ret["title"] = rt
                ret["abstract"] = description
                ret["tldr"] = ""
                ret["fieldOfStudy"] = categories
                ret["authors"] = [str(i) for i in authors]
                ret["references"] = []
                return ret
            return None
    return None