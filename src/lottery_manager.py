import tempfile
from datetime import datetime

import tweepy
import yaml

from infrastracture.local import FileRepositoryLocal
from log import logger
from settings import settings


# TODO のちにusecaseに移動
class LotteryManager:

    def __init__(self) -> None:
        auth = tweepy.OAuthHandler(settings.API_KEY, settings.API_SECRET)
        auth.set_access_token(settings.ACCESS_TOKEN, settings.ACCESS_TOKEN_SECRET)

        self._api = tweepy.API(auth)

    def lottery(self):
        # TODO あとで書く
        # 出力結果はymlかcsvか何かにする予定
        api = self._api

        logger.error('test')

        winners = {
            '@test_1': None,
            '@test_2': None,
        }

        file_repo = FileRepositoryLocal()

        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as tf:
            yaml.dump(winners, tf, encoding='utf-8', allow_unicode=True)

            now_str = datetime.now().strftime('%Y%m%d%H%M%S')
            file_repo.upload(tf.name, f'winners_{now_str}.yml')

        # user = api.get_user(screen_name="test")
        # tweets = api.search_tweets(q=['Python'], count=10)

        # for tweet in tweets:
        #     print('-----------------')
        #     print(tweet.text)
