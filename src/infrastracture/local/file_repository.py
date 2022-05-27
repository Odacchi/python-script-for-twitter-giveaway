import datetime
import glob
import os
import shutil
from typing import Optional, List

from settings import settings
from domain.file import FileRepository, Content


class FileRepositoryLocal(FileRepository):

    def __init__(self, base_path=None) -> None:
        self.base_path = f'{settings.DATA_DIR}/tmp' if base_path is None else base_path

    def upload(self, file_path: str, object_key: str):
        # object_keyがxxx/yyy.txtのような形式の場合xxxディレクトリがなくてもxxxディレクトリが自動生成される
        required_dir = f'{self.base_path}/{os.path.dirname(object_key)}'
        os.makedirs(required_dir, exist_ok=True)
        shutil.copyfile(file_path, self._get_full_path(object_key))

    def exists(self, object_key: str) -> bool:
        return os.path.exists(self._get_full_path(object_key))

    def download(self, object_key: str, save_path: str):
        shutil.copy(self._get_full_path(object_key), save_path)

    def delete(self, object_key: str):
        os.remove(self._get_full_path(object_key))

    def get_contents(self, object_key_prefix: str = None) -> List[Content]:
        search_str = f'{object_key_prefix}/*' if object_key_prefix else '*'
        file_dir_paths = glob.glob(self._get_full_path(search_str))
        if len(file_dir_paths) == 0:
            return []

        results = []
        for file_dir_path in file_dir_paths:
            name: str = os.path.basename(file_dir_path)
            object_key: str = f'{object_key_prefix}/{name}' if object_key_prefix else name
            is_file: bool = os.path.isfile(file_dir_path)
            updated_at_float = os.path.getmtime(file_dir_path)  # 更新日時
            updated_at = datetime.datetime.fromtimestamp(updated_at_float)
            # updated_at = os.path.getctime(file_dir_path) # 作成日時
            # updated_at = datetime.datetime.strptime(updated_at_str, '%Y%m%d%H%M%S')

            results.append(Content(name=name, object_key=object_key, is_file=is_file, updated_at=updated_at))

        # latest_file_path = max(file_paths, key=os.path.getctime)
        return results

    def _get_full_path(self, path: str):
        if path:
            return f'{self.base_path}/{path}'
        else:
            return self.base_path
