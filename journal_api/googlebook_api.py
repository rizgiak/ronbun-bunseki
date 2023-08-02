"""
googlebook_api
"""

import yaml
import requests
from thefuzz import fuzz

with open("settings.yaml") as yaml_file:
    settings = yaml.safe_load(yaml_file)

def search_books(title):
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": f"intitle:{title}",
        "maxResults": 5,  # Number of results to retrieve
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

            rt = book_title + " " + book_subtitle
            if fuzz.ratio(title.lower(), rt.lower()) > 95:
                return {"title": rt, "authors": authors, "desc": description}
            return ""
    else:
        return ""