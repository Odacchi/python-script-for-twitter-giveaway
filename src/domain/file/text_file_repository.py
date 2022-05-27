from abc import abstractmethod
from contextlib import contextmanager
from io import TextIOWrapper

from domain.file import FileRepository


class TextFileRepository(FileRepository):

    @abstractmethod
    @contextmanager
    def open(self, object_key: str, **kwargs) -> TextIOWrapper:
        """テキストファイルをテキストモードでオープンする。"""
        pass
