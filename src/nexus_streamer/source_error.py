from typing import Optional


class BadSource(Exception):
    def __init__(self, message: Optional[str] = None):
        if message is not None:
            self._message = message
        else:
            self._message = (
                "One or more critical problems with data source, see logs for details"
            )

    def __str__(self):
        return self._message
