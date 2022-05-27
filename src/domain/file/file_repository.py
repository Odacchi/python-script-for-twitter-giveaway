from abc import ABC, abstractmethod
from typing import Optional, List

from domain.file import Content


class FileRepository(ABC):

    @abstractmethod
    def upload(self, file_path: str, object_key: str):
        f"""{file_path}のファイルをリポジトリの{object_key}にアップロードする。"""
        pass

    @abstractmethod
    def download(self, object_key: str, save_path: str):
        f"""ファイルをリポジトリの{object_key}から{save_path}へダウンロードする。"""
        pass

    @abstractmethod
    def exists(self, object_key: str) -> bool:
        f"""リポジトリの{object_key}に既にファイルが存在するかを返す。"""
        pass

    @abstractmethod
    def delete(self, object_key: str):
        f"""リポジトリの{object_key}にあるオブジェクト（ファイル等）を削除する。"""

    @abstractmethod
    def get_contents(self, object_key_prefix: str = None) -> List[Content]:
        """ファイルおよびディレクトリの一覧を取得する。"""
        pass

    def get_file_contents(self, object_key_prefix: str) -> List[Content]:
        """ファイルの一覧を取得する。"""
        contents = self.get_contents(object_key_prefix)
        return list(filter(lambda content: content.is_file, contents))

    def get_dir_contents(self, object_key_prefix: str) -> List[Content]:
        """ディレクトリの一覧を取得する。"""
        contents = self.get_contents(object_key_prefix)
        return list(filter(lambda content: not content.is_file, contents))

    def get_latest_object_key(self, object_key_prefix: str) -> Optional[str]:
        f"""リポジトリのキーのプレフィックスから最終更新日のファイルを取得する。

        ex.
        csv/test/a.csv
        csv/test/b.csv
        csv/test/c.csv

        という構造にファイルが置かれている場合、{object_key_prefix}は csv/test を指定する。
        """
        file_contents = self.get_file_contents(object_key_prefix)

        latest_content = max(file_contents, key=lambda _content: _content.updated_at)
        return latest_content.object_key
