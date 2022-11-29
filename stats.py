from util import AutoVivification

class fitness:
    def __init__(self):
        self.cpuUtilizationRate = AutoVivification()
        self.memUtilizationRate = AutoVivification()
    def get_cpu_utilization_rate(topology):
        for node in topology.get_nodes():
            self.cpuUtilizationRate[node[0]] = topology.nodeServiceStores[node[0]] 
            