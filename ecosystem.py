import logging




class Sensor:
    pass


class Service:
    def __init__(self, cpu, memory, name, consumers, producers,  logger=None):
        # G is a nx.networkx graph
        self.name = name
        self.memory = memory
        self.cpu = cpu
        self.consumers = consumers
        self.producers = producers
        self.logger = logger or logging.getLogger(__name__)


class request:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)