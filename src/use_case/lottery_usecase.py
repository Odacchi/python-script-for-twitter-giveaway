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
    DEFAULT_PFP_IMAGE = 'https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png'

    def __init__(self) -> None:
        self.total_filtered = 0
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

        candidates = self._get_winner_candidates(tweet_url, conditions)

        winner_usernames = self._pickup_winners(num_of_winners, candidates, conditions)

        self._save_results(winner_usernames)

    def _pickup_winners(self,
                        num_of_winners: int, candidates: List[User], conditions: Optional[Dict] = None) -> List[str]:
        winner_usernames = []
        while len(winner_usernames) < num_of_winners:
            if not candidates:
                logger.debug(f'参加者不足のため終了！当選者数：{len(winner_usernames)}')
                break

            winner_candidate = random.choice(candidates)
            candidates.remove(winner_candidate)

            if winner_candidate.username not in winner_usernames:
                if self._is_valid_candidate(winner_candidate, conditions):
                    winner_usernames.append(winner_candidate.username)
            else:
                # ここに来ることはないはずだが一応
                logger.warning(f'{winner_candidate.username}は重複のためスキップ')
        return winner_usernames

    def _filter_candidates(self, candidates: List[User], conditions: Optional[Dict] = None) -> List[User]:
        if not conditions:
            # 条件指定なしならそのまま返す
            return candidates

        follower_lower_limit = conditions.get('follower_lower_limit', 0)
        must_have_pfp = conditions.get('must_have_pfp', False)

        filtered_candidates: List[User] = []
        for user in candidates:
            public_metrics: Dict = user.public_metrics
            if public_metrics is None:
                raise ValueError('Invalid API response')
                # logger.warning(f'[REJECT] Empty response... {user.username}')

            followers_count = public_metrics.get('followers_count', 0)
            if follower_lower_limit and followers_count < follower_lower_limit:
                logger.debug(f'[REJECT] {user.username} has too few followers: {followers_count}')
                self.total_filtered += 1
                continue

            if must_have_pfp and user.profile_image_url == self.DEFAULT_PFP_IMAGE:
                logger.debug(f'[REJECT] {user.username} has no PFP')
                self.total_filtered += 1
                continue

            filtered_candidates.append(user)

        return filtered_candidates

    def _is_valid_candidate(self, winner_candidate: User, conditions: Optional[Dict] = None):
        if not conditions:
            # 条件指定なしならTrue
            return True

        # follower_lower_limit = conditions.get('follower_lower_limit', 0)
        # must_have_pfp = conditions.get('must_have_pfp', False)
        #
        # try:
        #     response = self._client.get_user(id=winner_candidate.id,
        #                                      user_fields='profile_image_url,description,public_metrics')
        #     # response = self._client.get_users(id=[winner_candidate.id])
        #     user: User = response.data
        #     public_metrics: Dict = user.public_metrics
        #     if public_metrics is None:
        #         logger.warning(f'[REJECT] Empty response... {winner_candidate.username}')
        #         return False
        #
        #     followers_count = public_metrics.get('followers_count', 0)
        #
        #     if follower_lower_limit and followers_count < follower_lower_limit:
        #         logger.debug(f'[REJECT] {winner_candidate.username} has too few followers: {followers_count}')
        #         return False
        #
        #     if must_have_pfp and not user.profile_image_url:
        #         logger.debug(f'[REJECT] {winner_candidate.username} has no PFP')
        #         return False
        #
        #     time.sleep(1)  # APIを高速で叩くのを予防
        #
        # except Exception:
        #     logger.exception('on call get_followers')
        #     raise

        logger.debug(f"[WINNER] {winner_candidate.username} is winner")
        return True

    def _get_winner_candidates(self, tweet_url: str, conditions: Optional[Dict] = None) -> List[User]:
        client = self._client
        tweet_id = tweet_url.rsplit('/', 1)[1]

        next_token = None
        retweet_user_by_each_id: Dict[int, User] = {}
        try:
            while True:
                response = client.get_retweeters(tweet_id,
                                                 pagination_token=next_token, max_results=100,
                                                 user_fields='profile_image_url,description,public_metrics')
                retweet_users = response.data
                if retweet_users:
                    filtered_rt_users = self._filter_candidates(retweet_users, conditions)
                    retweet_user_by_each_id.update({_user.id: _user for _user in filtered_rt_users})
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
        candidate_by_each_id: Dict[User] = dict(
            filter(lambda item: item[0] in candidate_ids, retweet_user_by_each_id.items()))

        if conditions:
            follower_ids = set([])
            must_follows = conditions.get('must_follow', [])
            if len(must_follows) > 0:
                for must_follow_user_name in must_follows:
                    follower_ids.update(self._get_follower_ids(must_follow_user_name))

                candidate_by_each_id: Dict[User] = dict(
                    filter(lambda item: item[0] in follower_ids, candidate_by_each_id.items()))

        candidates = list(candidate_by_each_id.values())
        logger.debug(f'=======================================')
        logger.debug(f'Num of candidates: {len(candidates)}, Num of rejected: {self.total_filtered}')
        logger.debug(f'=======================================')
        return candidates

    def _get_follower_ids(self, user_name: str) -> Set[int]:
        call_count = 0

        follower_ids: Set[int] = set([])
        next_token = None
        try:
            while True:
                response = self._client.get_user(username=user_name)
                user: User = response.data
                call_count += 1
                # TODO 15分間に15リクエストまでしか受け付けないため他に良い方法ないか探す
                response = self._client.get_users_followers(user.id, pagination_token=next_token, max_results=1000)
                followers = response.data
                if followers:
                    follower_ids.update({follower.id for follower in followers})
                next_token = response.meta.get('next_token')
                if not next_token:
                    break

                time.sleep(1)
        except Exception:
            logger.exception(f'on call get_users_followers of {user_name}. call_count: {call_count}')
            raise

        return follower_ids

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
