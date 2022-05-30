import os
import yaml


class Config:
    num_of_winners: int
    tweet_url: str

    def __init__(self) -> None:
        yaml_path = f'{os.path.dirname(__file__)}/../data/config/config.yml'
        _config = yaml.safe_load(open(yaml_path))

        self.num_of_winners = _config.get('num_of_winners')
        self.tweet_url = _config.get('tweet_url')
        self.conditions = _config.get('conditions')


config = Config()
