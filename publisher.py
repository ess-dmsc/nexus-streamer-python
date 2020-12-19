from typing import Union


class LogDataPublisher:
    def __init__(self):
        pass

    def publish(self, data):
        pass


class EventDataPublisher:
    def __init__(self):
        pass

    def publish(self, data):
        pass


Publisher = Union[LogDataPublisher, EventDataPublisher]
