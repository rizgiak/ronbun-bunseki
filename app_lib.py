import json
import pandas as pd
import yaml
import logging
import logging.config

with open("settings.yaml") as yaml_file:
    settings = yaml.safe_load(yaml_file)

with open('logging_config.yaml', 'r') as config_file:
    log_config = yaml.safe_load(config_file)

logging.config.dictConfig(log_config)

class AppLib:
    def __init__(self) -> None:
        self.load_data()
    
    def search(self, id):
        title = self._st["nodes"][id]["name"]
        result = self._df[self._df["title"] == title]
        if len(result) > 0:
            return result.iloc[0].to_dict()
        else:
            logging.error(f"AppLib.search: Not found! title={title}")
            return {}

    def load_data(self):
        with open(settings["DF_DATA"], 'r') as file:
            data = json.load(file)
            self._df = pd.DataFrame(data)
        with open(settings["ST_DATA"], 'r') as json_file:
            self._st = json.load(json_file)
        return "OK"

    def get_st(self):
        return self._st
    

    