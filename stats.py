from util import AutoVivification

class Statistics:
    def __init__(self):
        self.cpuUtilizationRates = AutoVivification()
        self.memUtilizationRates = AutoVivification()
        self.request = AutoVivification()
        self.averageIntraResponseTime = 0
        self.intraPacketCount = 0
        self.averageCPUUtilizationRate = 0 
        self.averageMEMUtilizationRate = 0
        self.endtime = 0
        self.starttime = 0
        self.CLOUD_REQS = 0

    def get_cpu_utilization_rate(self,topology):
        for node in topology.get_compute_nodes():
            self.cpuUtilizationRates[node[0]] = topology.nodeServiceStores[node[0]] 
    
    def get_cpu_utilization_rate(self,topology):
        for node in topology.get_nodes():
            self.cpuUtilizationRates[node[0]] = topology.nodeServiceStores[node[0]] 
            
    def get_average_intra_latency(self):
        return self.averageIntraResponseTime

    def calculate_average_response_time(self,requests):
        count = 0
        sum = 0
        for request in requests:
            sum += request.latency
            count += 1
        return sum/count
