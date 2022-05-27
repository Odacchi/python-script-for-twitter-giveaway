from src.domain.app_exception import AppException


class FileNotFoundException(AppException):
    def message(self) -> str:
        return 'ファイルが存在しません。'


class IllegalFileFormatException(AppException):
    def message(self) -> str:
        return 'ファイルのフォーマットが不正です。'
