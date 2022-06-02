from abc import ABC
from typing import Optional, Dict, List

from tweepy import User


class CandidatesQueryService(ABC):
    def find_candidates(self, tweet_url: str, conditions: Optional[Dict] = None) -> List[User]:
        pass
