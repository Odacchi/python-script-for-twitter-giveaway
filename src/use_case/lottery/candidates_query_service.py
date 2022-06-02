import time
from abc import abstractmethod
from http.client import TOO_MANY_REQUESTS
from typing import List, Optional, Dict, Set

import tweepy
from tweepy import User

from infrastracture.twitter_api.candidates_query_service import CandidatesQueryService
from log import logger
from settings import settings


class CandidatesQueryServiceImpl(CandidatesQueryService):
    DEFAULT_PFP_IMAGE = 'https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png'

    def __init__(self) -> None:
        client = tweepy.Client(settings.BEARER_TOKEN)
        self._client = client
        self.total_filtered = 0

    def find_candidates(self, tweet_url: str, conditions: Optional[Dict] = None) -> List[User]:
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

        retweet_users = list(retweet_user_by_each_id.values())

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

        rt_and_liking_users = self._filter_users_by_ids(retweet_users, liking_user_ids)
        candidates = rt_and_liking_users

        if conditions:
            follower_ids = set([])
            must_follows = conditions.get('must_follow', [])
            if len(must_follows) > 0:
                for must_follow_user_name in must_follows:
                    follower_ids.update(self._get_follower_ids(must_follow_user_name))

                candidates: List[User] = list(filter(lambda user: user.id in follower_ids, rt_and_liking_users))

        logger.debug(f'=======================================')
        logger.debug(f'Num of candidates: {len(candidates)}, Num of rejected: {self.total_filtered}')
        logger.debug(f'=======================================')
        return candidates

    def _filter_candidates(self, candidates: List[User], conditions: Optional[Dict] = None) -> List[User]:
        if not conditions:
            # 条件指定なしならそのまま返す
            return candidates

        follower_lower_limit = conditions.get('follower_lower_limit', 0)
        must_have_pfp = conditions.get('must_have_pfp', False)
        exclude_users = conditions.get('exclude', [])

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

            if exclude_users and user.username in exclude_users:
                logger.debug(f'[REJECT] {user.username} is excluded user')
                self.total_filtered += 1
                continue

            filtered_candidates.append(user)

        return filtered_candidates

    def _get_follower_ids(self, user_name: str) -> Set[int]:
        call_count = 0

        follower_ids: Set[int] = set([])
        next_token = None
        try:
            while True:
                try:
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
                except tweepy.TooManyRequests:
                    wait_time = 60  # seconds
                    logger.debug(f'=======================================')
                    logger.debug(f'Too many request: call_count: {call_count}.')
                    logger.debug(
                        f'API (get_users_followers) call is retried after {wait_time} seconds '
                        f'due to request limitation.')
                    time.sleep(wait_time)
                    logger.debug(f'Now call the API again with "{next_token}" for the next token.')
        except Exception:
            logger.exception(f'on call get_users_followers of {user_name}. call_count: {call_count}')
            raise

        return follower_ids

    def _filter_users_by_ids(self, users: List[User], filter_user_ids: Set[int]) -> List[User]:
        filtered_users: List[User] = list(filter(lambda user: user.id in filter_user_ids, users))
        return filtered_users
