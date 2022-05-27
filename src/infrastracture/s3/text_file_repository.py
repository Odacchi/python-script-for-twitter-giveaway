import io
from contextlib import contextmanager
from io import TextIOWrapper

from domain.file.text_file_repository import TextFileRepository
from infrastracture.s3 import FileRepositoryS3


class TextFileRepositoryS3(FileRepositoryS3, TextFileRepository):

    @contextmanager
    def open(self, object_key: str, **kwargs) -> TextIOWrapper:
        with io.BytesIO() as stream:
            try:
                self._bucket.download_fileobj(object_key, stream)
                stream.seek(0)
                yield TextIOWrapper(stream, **kwargs)
            except Exception:
                raise

        # print('file close')
