from datetime import datetime


class Content:
    """File and Directory entity."""

    def __init__(
            self,
            name: str,
            object_key: str,
            is_file: bool,
            updated_at: datetime,
    ):
        self.name: str = name
        self.object_key: str = object_key
        self.is_file: bool = is_file
        self.updated_at: datetime = updated_at

    def __str__(self) -> str:
        return self.object_key

    # def __eq__(self, o: object) -> bool:
    #     if isinstance(o, Content):
    #         return self.object_key == o.object_key
    #
    #     return False

    # def is_xxx(self) -> bool:
    #     return self.xxx == self.read_xxx
