from contextlib import contextmanager
from io import TextIOWrapper

from domain.file.text_file_repository import TextFileRepository
from infrastracture.local import FileRepositoryLocal


class TextFileRepositoryLocal(FileRepositoryLocal, TextFileRepository):

    @contextmanager
    def open(self, object_key: str, **kwargs) -> TextIOWrapper:
        if not object_key:
            raise ValueError('Empty object_key is invalid.')

        file_path = self._get_full_path(object_key)

        with open(file_path, **kwargs) as stream:
            if type(stream) is not TextIOWrapper:
                raise ValueError('Invalid **kwargs parameter. Text mode only available.')
            yield stream

        # print('stream close')
