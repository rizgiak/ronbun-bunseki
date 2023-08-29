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
        with open('data/output_1.json', 'r') as file:
            data = json.load(file)
            self.df = pd.DataFrame(data)
    
    def search(self, title):
        result = self.df[self.df["title"] == title]
        if len(result) > 0:
            return result.iloc[0].to_dict()
        else:
            logging.error(f"AppLib.search: Not found! title={title}")
            return {}
    

    