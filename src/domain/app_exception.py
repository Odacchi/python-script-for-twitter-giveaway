from abc import ABC, abstractmethod


class AppException(Exception, ABC):
    """アプリケーションレベルの例外基底クラス"""

    @abstractmethod
    def message(self) -> str:
        pass

    def __str__(self):
        return self.message()
