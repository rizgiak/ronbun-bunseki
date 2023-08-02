"""
Utility
"""
# pylint: disable=C0103
import re
import json
from journal_api import arxiv_api
from journal_api import googlebook_api
import numpy as np
import pandas as pd


# Import Keyword Extractor KeyBERT
from keybert import KeyBERT
import yake


def _cut_text_between_patterns(text, start_pattern, end_pattern):
    """
    cut_text_between_patterns
    """
    pattern = re.escape(start_pattern) + r"(.*?)" + re.escape(end_pattern)
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    return ""


def abstract_extraction(text):
    """
    abstract_extraction
    """
    text = text.lower()
    start_pattern = "abstract"
    end_pattern = "introduction"
    result = _cut_text_between_patterns(text, start_pattern, end_pattern)
    return result


def metadata_extraction(text):
    """
    metadata_extraction
    """
    data = json.loads(text)
    return data


def keywords_extraction(text):
    """
    keywords_extraction
    """
    # Create candidates
    kw_extractor = yake.KeywordExtractor(top=100)
    candidates = kw_extractor.extract_keywords(text)
    candidates = [candidate[0] for candidate in candidates]

    i = 0
    for candidate in candidates:
        candidates[i] = candidate.lower()
        i += 1

    # Pass candidates to KeyBERT
    kw_model = KeyBERT(model="all-mpnet-base-v2")
    keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 10),
        candidates=candidates,
        stop_words="english",
        use_mmr=True,
        diversity=0.4,
    )
    return keywords


def generate_data_from_arxiv(df):
    df["arxiv"] = np.full(len(df), False).tolist()
    for idx, ref in df.iterrows():
        if ref["crossref"] == False:
            sc = arxiv_api.search(ref["title"])
            if sc != "":
                df.at[idx, "doi"] = sc.entry_id
                df.at[idx, "authors"] = [author.name for author in sc.authors]
                df.at[idx, "arxiv"] = True
    return df


def generate_data_from_gbooks(df):
    df["gbooks"] = np.full(len(df), False).tolist()
    for idx, ref in df.iterrows():
        if ref["crossref"] == False and ref["arxiv"] == False :
            sc = googlebook_api.search_books(ref["title"])
            if sc != "":
                df.at[idx, "authors"] = [author for author in sc["authors"]]
                df.at[idx, "gbooks"] = True
    return df


def string_to_df(str):
    str_json = json.loads(str)
    str_pd = pd.DataFrame(str_json)
    str_pd.index = str_pd.index.astype(int)
    return str_pd