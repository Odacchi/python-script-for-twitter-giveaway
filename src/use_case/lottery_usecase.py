import csv
import random
import tempfile
import time
from datetime import datetime
from typing import List, Optional, Dict, Set

import tweepy
from tweepy import User

from infrastracture.local import FileRepositoryLocal
from log import logger
from settings import settings


class LotteryUseCase:

    def __init__(self) -> None:
        # こっちだと、認証がうまくいかない
        # auth = tweepy.OAuthHandler(settings.API_KEY, settings.API_SECRET)
        # auth.set_access_token(settings.ACCESS_TOKEN, settings.ACCESS_TOKEN_SECRET)
        # self._api = tweepy.API(auth)
        # client = tweepy.Client(consumer_key=settings.API_KEY, consumer_secret=settings.API_SECRET,
        #                        access_token=settings.ACCESS_TOKEN, access_token_secret=settings.ACCESS_TOKEN_SECRET)

        client = tweepy.Client(settings.BEARER_TOKEN)
        self._client = client

    def lottery(self, tweet_url: str, num_of_winners: int, conditions: Optional[Dict] = None):
        """当選者を選出する。"""

        candidates = self._get_winner_candidates(tweet_url)

        winner_usernames = self._pickup_winners(num_of_winners, candidates, conditions)

        self._save_results(winner_usernames)

    def _pickup_winners(self,
                        num_of_winners: int, retweeters: List[User], conditions: Optional[Dict] = None) -> List[str]:
        winner_usernames = []
        while len(winner_usernames) < num_of_winners:
            if not retweeters:
                logger.debug(f'参加者不足のため終了！当選者数：{len(winner_usernames)}')
                break

            winner_candidate = random.choice(retweeters)
            retweeters.remove(winner_candidate)

            if winner_candidate.username not in winner_usernames:
                if self._is_valid_candidate(winner_candidate, conditions):
                    winner_usernames.append(winner_candidate.username)
            else:
                # ここに来ることはないはずだが一応
                logger.warning(f'{winner_candidate.username}は重複のためスキップ')
        return winner_usernames

    def _is_valid_candidate(self, winner_candidate: User, conditions: Optional[Dict] = None):
        if conditions is None:
            # 条件指定なしならTrue
            return True

        follower_lower_limit = conditions.get('follower_lower_limit')
        if follower_lower_limit > 0:
            try:
                response = self._client.get_users_followers(id=winner_candidate.id)
                followers = response.data
                if len(followers) < follower_lower_limit:
                    logger.debug(f'[REJECT] {winner_candidate.username} is has too few followers: {len(followers)}')
                    return False
                time.sleep(1)  # APIを高速で叩くのを予防

            except Exception:
                logger.exception('on call get_followers')
                raise

        logger.debug(f"[WINNER] {winner_candidate.username} is winner")
        return True

    def _get_winner_candidates(self, tweet_url) -> List[User]:
        client = self._client
        tweet_id = tweet_url.rsplit('/', 1)[1]

        next_token = None
        retweet_user_by_each_id: Dict[int, User] = {}
        try:
            while True:
                response = client.get_retweeters(tweet_id, pagination_token=next_token, max_results=100)

                retweet_users = response.data
                if retweet_users:
                    retweet_user_by_each_id.update({retweet_user.id: retweet_user for retweet_user in retweet_users})
                next_token = response.meta.get('next_token')
                if not next_token:
                    break
        except Exception:
            logger.exception('on call get_retweeters')
            raise

        liking_user_ids: Set[int] = set([])
        like_next_token = None
        try:
            while True:
                response = client.get_liking_users(tweet_id, pagination_token=like_next_token, max_results=100)

                liking_users = response.data
                if liking_users:
                    liking_user_ids.update({liking_user.id for liking_user in liking_users})
                like_next_token = response.meta.get('next_token')
                if not like_next_token:
                    break
        except Exception:
            logger.exception('on call get_liking_users')
            raise
        # 積集合
        candidate_ids = retweet_user_by_each_id.keys() & liking_user_ids
        candidate_by_each_id = dict(filter(lambda item: item[0] in candidate_ids, retweet_user_by_each_id.items()))

        candidates = list(candidate_by_each_id.values())

        logger.debug(f'Num of candidates: {len(candidates)}')
        return candidates

    @staticmethod
    def _save_results(winner_usernames):
        """抽選結果を保存する。"""
        csv_header = ['user_name', 'principal ID']
        csv_rows = [[f'@{username}', None] for username in winner_usernames]
        file_repo = FileRepositoryLocal()
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as tf:
            writer = csv.writer(tf)
            writer.writerow(csv_header)
            writer.writerows(csv_rows)
            tf.seek(0)
            # yaml.dump(winner_usernames, tf, encoding='utf-8', allow_unicode=True)

            now_str = datetime.now().strftime('%Y%m%d%H%M%S')
            file_repo.upload(tf.name, f'winners_{now_str}.csv')
