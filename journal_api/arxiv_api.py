"""
arxiv_api
"""

import arxiv

def search(title):
  search = arxiv.Search(
    query = title,
    max_results = 1,
    sort_by = arxiv.SortCriterion.Relevance
  )
  ret = ""
  for result in search.results():
    if result.title.lower() == title.lower():
      ret = result
  return ret