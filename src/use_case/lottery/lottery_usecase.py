import csv
import random
import tempfile
from datetime import datetime
from typing import List, Optional, Dict

from tweepy import User

from infrastracture.local import FileRepositoryLocal
from infrastracture.twitter_api.candidates_query_service import CandidatesQueryService
from log import logger
from use_case.lottery.candidates_query_service import CandidatesQueryServiceImpl


class LotteryUseCase:

    def __init__(self) -> None:
        # こっちだと、認証がうまくいかない
        # auth = tweepy.OAuthHandler(settings.API_KEY, settings.API_SECRET)
        # auth.set_access_token(settings.ACCESS_TOKEN, settings.ACCESS_TOKEN_SECRET)
        # self._api = tweepy.API(auth)
        # client = tweepy.Client(consumer_key=settings.API_KEY, consumer_secret=settings.API_SECRET,
        #                        access_token=settings.ACCESS_TOKEN, access_token_secret=settings.ACCESS_TOKEN_SECRET)

        self._candidates_query_service: CandidatesQueryService = CandidatesQueryServiceImpl()

    def lottery(self, tweet_url: str, num_of_winners: int, conditions: Optional[Dict] = None):
        """当選者を選出する。"""

        candidates = self._candidates_query_service.find_candidates(tweet_url, conditions)

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

    def _is_valid_candidate(self, winner_candidate: User, conditions: Optional[Dict] = None):
        if not conditions:
            # 条件指定なしならTrue
            return True

        logger.debug(f"[WINNER] {winner_candidate.username} is winner")
        return True

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
