from config import config
from use_case.lottery.lottery_usecase import LotteryUseCase


def main():
    lottery_use_case = LotteryUseCase()
    lottery_use_case.lottery(config.tweet_url, config.num_of_winners, config.conditions)


if __name__ == '__main__':
    main()
