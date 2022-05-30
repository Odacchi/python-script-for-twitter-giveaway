import sys

from config import config
from lottery_manager import LotteryManager


def main():
    lottery_manager = LotteryManager()
    lottery_manager.lottery(config.tweet_url, config.num_of_winners, config.conditions)


if __name__ == '__main__':
    main()
