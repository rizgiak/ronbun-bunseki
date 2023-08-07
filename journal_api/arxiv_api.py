"""
arxiv_api
"""

import arxiv
import string
from thefuzz import fuzz

def _remove_punctuation(text):
    translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    return text.translate(translator)

def search(title):
  title_rm = _remove_punctuation(title)
  
  search = arxiv.Search(
    query = title_rm,
    max_results = 1,
    sort_by = arxiv.SortCriterion.Relevance
  )
  
  for result in search.results():
    if fuzz.token_set_ratio(title.lower(), result.title.lower()) == 100:
      ret = {}
      ret["title"] = result.title
      ret["abstract"] = result.summary
      ret["tldr"] = ""
      ret["fieldOfStudy"] = result.categories
      ret["authors"] = [str(i) for i in result.authors]
      ret["references"] = []
      return ret
  return None