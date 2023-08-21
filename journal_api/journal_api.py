from journal_api import arxiv_api
from journal_api import crossref_api
from journal_api import googlebook_api
from journal_api import semanticscholar_api

class JournalAPI:
    def __init__(self):
        self._max_pos = 3

    def _dic_library(self, title, pos, year = 2010):
        res = None
        if pos == 1:
            res = crossref_api.search(title, year)
        elif pos == 2:
            res = arxiv_api.search(title, year)
        elif pos == 3:
            res = googlebook_api.search(title, year)
        else:
            res = semanticscholar_api.search(title, year) 
        return res

    def _remake_result(self, result, pos):
        if (result == None):
            return None
        dic = ["abstract", "year", "fieldsOfStudy", "authors", "references"]
        l   = [result[dic[0]] == "", result[dic[1]] == "", result[dic[2]] == "", len(result[dic[3]]) == 0, len(result[dic[4]]) == 0]

        if any(l): # data not completed
            for i in range(pos + 1, self._max_pos + 1):
                rc = self._dic_library(result["title"], i)
                if rc != None:
                    r = [rc["abstract"] == "", rc["year"] == "", rc["fieldsOfStudy"] == "", len(rc["authors"]) == 0, len(rc["references"]) == 0]
                    for index, value in enumerate(l):
                        if(value == True and r[index] == False):
                            l[index] = False
                            result[dic[index]] = rc[dic[index]]
                    if not any(l):
                        break

        return result

    def _fix_references(self, result, year):
        if (result == None):
            return None
        
        if len(result["references"]) > 0:
            refs = []
            for ti in (result["references"]):
                for i in range(self._max_pos + 1):
                    res = self._dic_library(ti, i, year)
                    if(res != None):
                        if res["year"] != "" and res["year"] >= year:
                            refs.append(ti)
                        break;
            result["references"] = refs
        return result

    def search(self, title, start_year = 2010, fix_references = True):
        res = None
        for i in range(self._max_pos + 1):
            res = self._dic_library(title, i, start_year)
            if (res != None and res["year"] != "" and res["year"] < start_year): # year limitation
                return None
            res = self._remake_result(res, i)
            if fix_references:
                res = self._fix_references(res, start_year)
            if(res != None):
                break;
        return res
