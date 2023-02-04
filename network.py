#===============================================================
# Network
# / This file is responsible for modeling the network
#===============================================================



import time

import logging
import math
import uuid
import json as js
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import simpy
import random
from simpy.util import start_delayed
from numba import jit, cuda

from simpy.resources.store import Store
from simpy.resources.store import FilterStore
from networkx.readwrite import json_graph
from collections import defaultdict
from util import AutoVivification
from stats import Statistics

#===============================================================
# Topology
# / This class is responsible for modeling network topology
#===============================================================


class Service:
    def __init__(self, id ,name, place, ram, cpu, needs, topology):
        self.id = id
        self.name = name
        self.place = place
        self.ram = ram
        self.cpu = cpu
        self.needs = needs
        self.usedCPU = 0
        self.usedMEM = 0
        self.serviceStore = simpy.FilterStore(topology.env)
        self.waitingStore = simpy.FilterStore(topology.env)


class Topology:
    """
    This class unifies the functions to deal with **Complex Networks** as a network topology within of the simulator. In addition, it facilitates its creation.
    """

    # LINK_LATENCY = "LATENCY"
    # " A edge or a network link has a Bandwidth"

    MEDIAN_BW = 1500

    SNR = 30

    def __init__(self, env, logger=None, *args, **kwargs):
        # G is a nx.networkx graph
        self.G = None
        self.nodeAttributes = {}
        self.linkStores = {}
        self.nodeStores = {}
        self.remainingMEM = {}
        self.remainingCPU = {}
        self.nodeServiceStores = {}
        self.transmitionQueues = {}
        self.recievedRequests = {}
        self.routingTable = AutoVivification()
        # self.serviceTable = AutoVivification()
        self.logger = logger or logging.getLogger(__name__)
        self.env = env
        self.placementTable = AutoVivification()
        self.internalQueues = {}
        self.averageReqLatency = 0
        self.stats = Statistics()
        self.APPS = AutoVivification()
        self.REQUEST_COUNT = 0
        self.FIRST_REQUEST = 0
        jsonFile = kwargs.get('jsonFile', None)
        self.stats = Statistics()
        if jsonFile is not None:
            self.load_cyjs(jsonFile)
        for link in self.get_links():
            self.linkStores[str(link[0])+'-'+str(link[1])] = simpy.Store(self.env)
            self.linkStores[str(link[1])+'-'+str(link[0])] = simpy.Store(self.env)
        for node in self.get_nodes():
            self.nodeStores[node[0]] = simpy.FilterStore(self.env)
            self.recievedRequests[node[0]] = simpy.Store(self.env)
            self.transmitionQueues[node[0]] = simpy.Store(self.env)
            self.internalQueues[node[0]] = simpy.FilterStore(self.env)
            # # #print(node[1])
            if node[1]['MODE'] == 'COMPUTE' or node[1]['MODE'] == 'CLOUD':
                self.nodeServiceStores[node[0]] = simpy.FilterStore(self.env)
                self.remainingMEM[node[0]] = node[1]['RAM']
                self.remainingCPU[node[0]] = node[1]['CPU']

    #===============================================================
    # service
    # / These are service placement related functions
    #===============================================================
    # def get_random_node(self, services):
    #     return 

    # def create_service_routing_table(self, services):
    #     for service in services:
    #         if len(service[1]['needs']) > 0:
    #             self.serviceTable[service[0]] = service[1]['needs']
    #     yield self.env.timeout(0)

    def get_cpu_utilization_rate(self, nodeID):
        
        node = self.get_node(nodeID)
        # if node[0] != nodeID:
        #     #print(node)
        #     #print(nodeID)
        rate = (node[1]['CPU'] - self.remainingCPU[nodeID])/node[1]['CPU']
        return rate
    
    def get_all_nodes_cpu_utilization_rate(self):
        #print(self.env.now, {node[0] : self.get_cpu_utilization_rate(node[0]) for node in self.get_compute_nodes() if node[0] != "CLOUD"})
        return {node[0] : self.get_cpu_utilization_rate(node[0]) for node in self.get_compute_nodes() if node[0] != "CLOUD"}
    
    def set_endtime(self, requests):
        endtime = 0
        for req in requests:
            if req.responseTime > endtime:
                endtime = req.responseTime
        self.stats.endtime = endtime

    def get_mem_utilization_rate(self, nodeID):
        node = self.get_node(nodeID)
        # if node[0] != nodeID:
        #     #print(node)
        #     #print(nodeID)
        rate = (node[1]['RAM'] - self.remainingMEM[nodeID])/node[1]['RAM']
        # if rate > 1:
        #     ##print("-------------------------")
        #     #print(node)
        #     #print(nodeID)
        #     #print(node[1]['RAM'])
        #     #print(self.remainingMEM[nodeID])
        return rate

    def get_all_nodes_mem_utilization_rate(self):
        return {node[0] : self.get_mem_utilization_rate(node[0]) for node in self.get_compute_nodes() if node[0] != "CLOUD"}
     
    def get_utilization_rates(self):
        #print("now ", str(self.env.now))
        self.stats.cpuUtilizationRates[str(self.env.now)] = self.get_all_nodes_cpu_utilization_rate()
        self.stats.memUtilizationRates[str(self.env.now)] = self.get_all_nodes_mem_utilization_rate()
        yield self.env.timeout(0)
        # yield 0
    
    
    def all_cpu_utilization_average(self):
        count = 0
        sum = dict()
        records =  {k: v for k, v in self.stats.cpuUtilizationRates.items() if float(k) < self.stats.endtime }
        # for node in self.get_compute_nodes():
        #     if node[0] != "CLOUD":
        #         sum[node[0]] = 0
        for record in records:
            sum[record] = 0
        # #print(records)
        nodeCount = len(self.get_compute_nodes()) - 1 
        recordCount = 0
        for record in records:
            for entry in records[record]:
                sum[record] += records[record][entry]
            recordCount += 1
        for record in sum:
            sum[record] = sum[record]/nodeCount
        All = 0
        for entry in sum:
            All += sum[entry]
        return All/recordCount

    
    def all_costs(self):
        runTime = self.stats.endtime - self.stats.starttime
        overallCostPerMin = 0
        for node in self.get_compute_nodes():
            overallCostPerMin += node[1]['COST']
        # # #print(overallCostPerMin)
        return (overallCostPerMin*runTime)/60
    
    
    def all_mem_utilization_average(self):
        count = 0
        sum = dict()
        records =  {k: v for k, v in self.stats.memUtilizationRates.items() if float(k) < self.stats.endtime }
        # for node in self.get_compute_nodes():
        #     if node[0] != "CLOUD":
        #         sum[node[0]] = 0
        for record in records:
            sum[record] = 0
        # #print(records)
        nodeCount = len(self.get_compute_nodes()) - 1 
        recordCount = 0
        for record in records:
            for entry in records[record]:
                sum[record] += records[record][entry]
            recordCount += 1
        for record in sum:
            sum[record] = sum[record]/nodeCount
        All = 0
        for entry in sum:
            All += sum[entry]
        return All/recordCount
    

    def all_mem_utilization(self):
        count = 0
        sum = dict()
        records =  {k: v for k, v in self.stats.memUtilizationRates.items() if float(k) < self.stats.endtime }
        nodeCount = len(self.get_compute_nodes()) - 1
        # for node in self.get_compute_nodes():
        #     if node[0] != "CLOUD":
        #         sum[node[0]] = 0
        for record in records:
            # #print("bug! ",records[record])
            sum[record] = 0
        # #print(records)
        recordCount = 0
        for record in records:
            for entry in records[record]:
                sum[record] += float(records[record][entry])
            recordCount += 1
        for record in sum:
            sum[record] = float(sum[record]/nodeCount)
        return sum

    #===============================================================
    # service
    # / These are service placement related functions
    #===============================================================

    def get_all_service_nodes(self, serviceName):
        # # #print(self.placementTable)
        # # #print({k: v for k, v in self.placementTable[serviceName]['deployments'] if v[1] > 0})
        return {k: v for k, v in self.placementTable[serviceName]['deployments'] if v[1] > 0}


    # def set_request_destination_node(self, nodeID, request):
    #     current = self.get_node(nodeID)
    #     for item in self.nodeServiceStores[current].items:
    #         if item.name == request.destinationService:
    #             return request.set_destination_node(nodeID)
    #     else:
    #         for node in self.get_all_service_nodes(current):
    #             pass

    def create_service_placement_table(self,NUM_APPS,NUM_SERVICES):

        for i in range(NUM_APPS):
            self.APPS['APP_'+str(i)] = []    

        for i in range(NUM_APPS):
            for j in range(NUM_SERVICES):
                self.APPS['APP_'+str(i)] += [['APP_'+str(i)+'_SERVICE_'+str(j),AutoVivification()]]
                if j != NUM_SERVICES-1:
                    self.APPS['APP_'+str(i)][j][1]['needs'] = ['APP_'+str(i)+'_SERVICE_'+str(j+1)]

        total_instances = 0
        instance_per_service = 2
        for app in self.APPS:
            for j in range(NUM_SERVICES):
                self.APPS[app][j][1]['instances'] = instance_per_service
                total_instances += self.APPS[app][j][1]['instances']
        # #print(total_instances)
        ram_per_instance = 8000*50/total_instances
        cpu_per_instance = 8*50/total_instances
        instance_per_device_ram = 8000/ram_per_instance
        instance_per_device_cpu = 8/cpu_per_instance
        # instance_per_service = int(min(instance_per_device_cpu, instance_per_device_ram))


        for i in range(NUM_APPS):
            for j in range(NUM_SERVICES):
                self.APPS['APP_'+str(i)][j][1]['RAM'] = round(ram_per_instance,2)
                self.APPS['APP_'+str(i)][j][1]['CPU'] = round(cpu_per_instance,2)

        for app in self.APPS:
            for service in self.APPS[app]:
                self.placementTable[service[0]] = service[1] 
                # #print(self.placementTable[service[0]])

        # self.placementTable['APP_0_SERVICE_0']['instances'] = 3
        # # #print(self.placementTable['APP_0_SERVICE_0'])
        for service in self.placementTable:
            for node in range(len(self.get_nodes())):
                self.placementTable[service]['deployments'][node]['replicas'] = 0

        compute_nodes = self.get_compute_nodes()
        node_map = []
        for i in range(len(compute_nodes)):
            node_map.append([])
        for service in self.placementTable:
            self.placementTable[service]['deployments']['CLOUD']['replicas'] = 100
            # #print(service)
            # #print(self.placementTable[service]['deployments'])
            for i in range(self.placementTable[service]['instances']):
                candidate_node_number = random.randrange(len(compute_nodes))
                candidate_node = node_map[candidate_node_number]
                while len(candidate_node) >= instance_per_service:
                    candidate_node_number = random.randrange(len(compute_nodes))
                    candidate_node = node_map[candidate_node_number]
                candidate_node += [service]
                
                # #print(self.placementTable[service]['deployments'])
                self.placementTable[service]['deployments'][compute_nodes[candidate_node_number][0]]['replicas'] += 1
            # #print('here')
        yield self.env.timeout(0)
        
    def get_nodes_with_service(self,current,serviceName,request):
        # # ##print("this", [v for v in self.placementTable[serviceName]['deployments'] if (self.placementTable[serviceName]['deployments'][v]['replicas'] > 0 and v not in request.history )])
        return [v for v in self.placementTable[serviceName]['deployments'] if (self.placementTable[serviceName]['deployments'][v]['replicas'] > 0 and v not in request.history )]
    
    
    def choose_request_destination(self, current, request):

        possibleDestination = [(node,nx.path_weight(G=self.G, path=self.routingTable[str(current)][str(node)][0], weight='COST')) for node in self.get_nodes_with_service(current,request.destinationService,request)]
        # # #print(possibleDestination)
        min = 100
        next = 0
        # # ##print("possible: ", possibleDestination)
        for dest in possibleDestination:
            if dest[1] < min:
                min = dest[1]
                next = dest[0]
        request.destinationNode = next
        # #print(request.id,"destination node unknown, setting to ",request.destinationNode, " at node ", current, " at ", self.env.now,"| Response: ", request.response)
        # yield self.env.timeout(0)
        # return next
            
    
    def place_services(self):
        for node in self.get_compute_nodes():
            for service in self.placementTable.keys():
                for index in range(self.placementTable[service]['deployments'][node[0]]['replicas']):
                    newService = Service(index,service,node[0],self.placementTable[service]['RAM'],self.placementTable[service]['CPU'],self.placementTable[service]['needs'], self)
                    # #print(newService.name, newService.id , " placed on node ", node[0])
                    yield self.nodeStores[node[0]].put(newService)

    #===============================================================
    # Node
    # / These are node related functions
    #===============================================================

    def get_nod_id(self, node):
        return node[0]

    def get_node(self, id):
        """
        Returns:
            node: get a graph node
        """
        for node in self.G.nodes(data=True):
            if node[0] == id:
                return node
    
    def get_routing_nodes(self):
        return [node for node in self.G.nodes(data=True) if node[1]['MODE'] != 'ZONE']

    def get_zones(self):
        return [node for node in self.G.nodes(data=True) if node[1]['MODE'] == 'ZONE']

    def get_nodes(self):
        """
        Returns:
            list: a list of graph nodes
        """
        return self.G.nodes(data=True)

    def get_neighbors(self, nodeID):
        return [str(neighbor) for neighbor in self.G.neighbors(nodeID)]


    def get_compute_nodes(self):
        """
        Returns:
            list: a list of compute nodes
        """
        return [node for node in self.get_nodes() if node[1]['MODE'] == 'COMPUTE'] + [node for node in self.get_nodes() if node[1]['MODE'] == 'CLOUD']

    def get_routers(self):
        """
        Returns:
            list: a list of fog routers
        """
        return [node for node in self.get_nodes(data=True) if node[1]['MODE'] == 'ROUTER']

    
    def compute_distance_between_two_nodes(self, source, target, _t):
        """
        Args:
            source (str): source node id
            target (str): destination node id
            _t: this is dummy variable, must remove later
        Returns:
            float: a float of distance between two nodes
        """
        nodes = []
        for node in self.get_nodes():
            if str(node[0]) == str(source) or str(node[0]) == str(target):
                nodes.append(node[1])
        # # #print(nodes)
        return math.hypot(nodes[1]['X'] - nodes[0]['X'], nodes[1]['Y'] - nodes[0]['Y'])

    #===============================================================
    # Links
    # / These are link related functions
    #===============================================================

    def get_links(self):
        """
        Returns:
            returns all links in the network
        """
        return self.G.edges(data=True)

    
    def get_link(self, source, target):
        """
        Args:
            source (str): source node id
            target (str): destination node id
        Returns:
            returns the desired link
        """
        for link in self.get_links():
            if (str(link[0]) == source and str(link[1]) == target) or (str(link[0]) == target and str(link[1]) == source):
                return link

        
    def get_link_bandwidth(self, source, target):
        """
        Args:
            source (str): source node id
            target (str): destination node id
        Returns:
            returns the bandwidth of the specified link using source and destination target
        """
        for link in self.get_links():
            if (str(link[0]) == source and str(link[1]) == target) or (str(link[0]) == target and str(link[1]) == source):
                return link[2]['bandwidth']

    
    def get_link_propagation_speed(self, source, target):
        """
        Args:
            source (str): source node id
            target (str): destination node id
        Returns:
            returns the propagation speed of the specified link using source and destination target
        """
        for link in self.get_links():
            if (str(link[0]) == str(source) and str(link[1]) == str(target)) or (str(link[0]) == str(target) and str(link[1]) == str(source)):
                return link[2]['PS']


    def get_link_bitrates(self):
        """
        Returns:
            returns all link bitrates
        """
        return [(str(link[0]),str(link[1]), self.calculate_bitrate(link)) for link in self.get_links()]

    def get_link_propagation_delay(self, source, target):
        """
        Args:
            source (str): source node id
            target (str): destination node id
        Returns:
            returns the propagation time of the specified link using source and destination target
        """
        return self.compute_distance_between_two_nodes(source, target, _t=None) / self.get_link_propagation_speed(source, target)

    def get_request_delivery_time(self, source, target, request):
        """
        Args:
            source (str): source node id
            target (str): destination node id
            request (request): request object
        Returns:
            returns the delievery time of the specified request on the specified link using source and destination target
        """
        return self.get_link_propagation_delay(source, target) + request.get_transmition_delay(source,target,self)

    def queue_request_for_transmition(self,current, request, time):
        self.REQUEST_COUNT += 1
        delay = time - self.env.now 
        if delay == 0:
            yield self.put_request_in_ts_queue(current, request) 
        else:
            yield start_delayed(self.env ,self.put_request_in_ts_queue(current, request), delay)


    def put_request_in_ts_queue(self, current, request):
        request.issueTime = self.env.now
        if self.FIRST_REQUEST == 0:
            self.FIRST_REQUEST = 1
            self.stats.starttime = self.env.now
        ##print("Putting request ", request.id ," on transmition queue in node ", current, " at ", str(self.env.now), "| Response: ", request.response)
        for node in self.get_nodes():
            if str(node[0]) == current:
                yield self.transmitionQueues[node[0]].put(request)

    def start_request_process(self, request, nodeID, serviceID, serviceName):
        node = self.get_node(nodeID)
        requestExecutionTime = (request.instructions / (node[1]['IPS'])*1.000)
        self.remainingCPU[nodeID] -= request.cpu
        self.remainingMEM[nodeID] -= request.ram
        for item in self.nodeStores[nodeID].items:
            if item.name == request.destinationService and item.id == serviceID:
                item.usedCPU += request.cpu
                item.usedMEM += request.ram
                item.cpu -= request.cpu
                item.ram -= request.ram
        # # #print(self.placementTable[serviceName]['needs'])
        if len(self.placementTable[serviceName]['needs']) > 0:
            for service in self.placementTable[serviceName]['needs']:
                request.satisfied += 1
                needs = Request(name='Issued by '+ serviceName, source=nodeID, destinationService=service ,size=request.size, instructions=request.instructions, cpu=request.cpu, ram=request.ram, sub=True, issuedBy=request.name, masterService=serviceName+'-'+str(serviceID), masterRequest=request.id, env= self.env)
                needs.issueTime = self.env.now
                self.transmitionQueues[nodeID].put(needs)
            for item in self.nodeStores[nodeID].items:
                if item.name == request.destinationService and item.id == serviceID:
                    item.waitingStore.put(request)
                    ##print("Request ", request.id, " needs ", request.satisfied," other services putting in waiting queue at ", request.destinationNode ," in service ", item.name, " at ", str(self.env.now))
                    break
        else:
            start_delayed(self.env ,self.finish_request(request=request, nodeID=nodeID, serviceID=serviceID, serviceName=serviceName), requestExecutionTime)


    def finish_request(self, request, nodeID, serviceID, serviceName):
        #print("request ", request.id ," finished on node: ", nodeID, " on service: ", serviceName, serviceID , " at ", self.env.now)
        # #print(self.remainingCPU[nodeID])
        # #print(self.remainingMEM[nodeID])
        # #print(len(self.nodeStores[nodeID].items))
        self.remainingCPU[nodeID] += request.cpu
        self.remainingMEM[nodeID] += request.ram
        for item in self.nodeStores[nodeID].items:
            if item.name == request.destinationService and item.id == serviceID:
                ##print("Computation of packet ", request.id, " Done in service ", item.name, item.id, " in ", request.destinationNode , " at ", str(self.env.now))
                # #print( request.id, " Sending response back to  ", request.source , " at ", str(self.env.now))
                item.usedCPU -= request.cpu
                item.usedMEM -= request.ram
                item.cpu += request.cpu
                item.ram += request.ram
                # #print(len(item.serviceStore.items))
                tttt = item.serviceStore.get(filter=lambda request: True)
                #print('used CPU by service: ', item.usedCPU)
                totalReqs = 0
                for item in self.nodeStores[nodeID].items:
                    totalReqs += len(item.serviceStore.items)
                #print(self.remainingCPU[nodeID])
                #print(self.remainingMEM[nodeID])
                #print("Total reqs in node ", nodeID ,totalReqs)
                # #print(len(item.serviceStore.items))
                # #print(tttt)
                request.response = True
                tmp = request.source
                request.source = request.destinationNode
                request.destinationNode = tmp
                totalReqs = 0
                yield self.transmitionQueues[nodeID].put(request)
                break

    def recieve_request(self, sender, reciever):
        # yield self.env.timeout(delay)
        request = yield self.linkStores[str(sender)+'-'+str(reciever)].get()  
        if str(request.destinationNode) == str(reciever):
            if request.response:
                request.responseTime = self.env.now
                ##print("Recieved response of packet ", request.id , request.name , " at ", reciever, " at ", str(self.env.now),"| Response: ", request.response)
                if request.sub:
                    masterService = request.masterService.split('-')[0]
                    masterId = request.masterService.split('-')[1]
                    for item in self.nodeStores[reciever].items:
                        if item.name == masterService and str(item.id) == masterId:
                            for waitingReq in item.waitingStore.items:
                                if waitingReq.id == request.masterRequest:
                                    waitingReq.satisfied -= 1
                                    ##print("One condition satisfied for ", waitingReq.id, " at ", reciever, " at ", str(self.env.now)) 
                                    if waitingReq.satisfied == 0: 
                                        ##print("All conditions satisfied for ", waitingReq.id, " at ", reciever, " at ", str(self.env.now)) 
                                        req = yield item.waitingStore.get(filter=lambda waitingReq: True)
                                        # # #print(item.waitingStore.items)
                                        node = self.get_node(reciever)
                                        requestExecutionTime = (req.instructions / (node[1]['IPS'])*1.000)
                                        start_delayed(self.env ,self.finish_request(request=req, nodeID=reciever, serviceID=int(masterId), serviceName=masterService), requestExecutionTime)
                                        break
                            #break
            else:
                ##print("Packet ", request.id, " reached destination ", reciever, " at ", str(self.env.now),"| Response: ", request.response)
                for item in self.nodeStores[reciever].items:
                    if item.name == request.destinationService:
                        if item.cpu >= request.cpu and item.ram >= request.ram:
                            request.latency = self.env.now - request.issueTime 
                            if request.sub:
                                count = self.stats.intraPacketCount
                                avg = self.stats.averageIntraResponseTime
                                if count == 0:
                                    self.stats.intraPacketCount = 1
                                    self.stats.averageIntraResponseTime = request.latency
                                else:
                                    self.stats.intraPacketCount = count + 1
                                    avg = ((self.stats.averageIntraResponseTime * count) + request.latency)/(count+1)
                                    self.stats.averageIntraResponseTime = avg
                            #print("Computation of packet ", request.id, " started in service ", item.name, item.id, " in ", request.destinationNode , " at ", str(self.env.now))
                            self.start_request_process(request=request, nodeID=reciever, serviceID=item.id, serviceName=item.name)
                            yield item.serviceStore.put(request)
                            break
                        # else: 
                            #print(reciever)
                            #print(self.remainingCPU[reciever], self.remainingMEM[reciever], self.env.now)
                            #print("No resource for request found on node ", request.id, reciever, type(reciever), " Service ", item.name , " at ", str(self.env.now) )
                else:
                    request.history += [request.destinationNode]
                    if request.failed >= 4:
                        request.destinationNode = 'CLOUD'
                        self.stats.CLOUD_REQS += 1
                    else:
                        request.destinationNode = 'NA'
                        request.failed += 1
                    ##print("No resource for request ", request.id, " on node", reciever, "...puting in queue at", str(self.env.now))
                    yield self.transmitionQueues[reciever].put(request)
        else:
            ##print("Packet ", request.id, " recieved at", reciever, "...puting in queue at", str(self.env.now),"| Response: ", request.response)
            yield self.transmitionQueues[reciever].put(request) 
    
    def get_cloud_reqs(self):
        return self.stats.CLOUD_REQS

    def recieve_internal_request(self, nodeID, request):
        yield self.internalQueues[nodeID].get(filter=lambda request: True) 
        if request.response:
            request.responseTime = self.env.now
            ##print("Recieved internal response of packet ", request.id, " at ", nodeID, " at ", str(self.env.now),"| Response: ", request.response)
            if request.sub:
                masterService = request.masterService.split('-')[0]
                masterId = request.masterService.split('-')[1]
                for item in self.nodeStores[nodeID].items:
                    # # #print(item.name+"-"+item.id)
                    if item.name == masterService and str(item.id) == masterId:
                        for waitingReq in item.waitingStore.items:
                            if waitingReq.id == request.masterRequest:
                                waitingReq.satisfied -= 1
                                ##print("One condition satisfied for ", waitingReq.id, " at ", nodeID, " at ", str(self.env.now)) 
                                if waitingReq.satisfied == 0:   
                                    ##print("All conditions satisfied for ", waitingReq.id, " at ", nodeID, " at ", str(self.env.now)) 
                                    req = yield item.waitingStore.get(filter=lambda waitingReq: True)
                                    node = self.get_node(nodeID)
                                    requestExecutionTime = (waitingReq.instructions / (node[1]['IPS'])*1.000)
                                    start_delayed(self.env ,self.finish_request(request=waitingReq, nodeID=nodeID, serviceID=int(masterId), serviceName=masterService), requestExecutionTime)
                                    break
        else:
            ##print("Packet ", request.id, " already at destination ", nodeID, " at ", str(self.env.now),"| Response: ", request.response)
            for item in self.nodeStores[nodeID].items:
                if item.name == request.destinationService:
                    # # #print(request.cpu)
                    if item.cpu >= request.cpu and item.ram >= request.ram:
                        request.latency = self.env.now - request.issueTime 
                        if request.sub:
                            count = self.stats.intraPacketCount 
                            avg = self.stats.averageIntraResponseTime
                            if count == 0:
                                self.stats.intraPacketCount = 1
                                self.stats.averageIntraResponseTime = request.latency
                            else:
                                self.stats.intraPacketCount = count + 1
                                avg = ((self.stats.averageIntraResponseTime * count) + request.latency)/(count+1)
                                self.stats.averageIntraResponseTime = avg
                        #print("Computation of packet ", request.id, " started in service ", item.name, item.id, " in ", request.destinationNode , " at ", str(self.env.now))
                        self.start_request_process(request=request, nodeID=nodeID, serviceID=item.id, serviceName=item.name)
                        yield item.serviceStore.put(request)
                        break
                    # else: 
                        #print(nodeID)
                        #print(self.remainingCPU[nodeID], self.remainingMEM[nodeID], self.env.now)
                        #print("No resource for request found on node ", request.id, nodeID, type(nodeID), " Service ", item.name , " at ", str(self.env.now) )

            else:
                request.history += [request.destinationNode]
                if request.failed >= 4:
                    request.destinationNode = 'CLOUD'
                    self.stats.CLOUD_REQS += 1
                else:
                    request.destinationNode = 'NA'
                    request.failed += 1
                ##print("No resource for request ", request.id, " on node", nodeID, "...puting in queue at", str(self.env.now))
                yield self.transmitionQueues[nodeID].put(request)
        return 

    def transmit_request(self, request, sender, reciever):
        # yield self.env.timeout(delay)
        ##print("Packet ", request.id, " transmited to ", reciever, " from ", sender, " at ", str(self.env.now),"| Response: ", request.response)
        yield self.linkStores[str(sender)+'-'+str(reciever)].put(request)
    

    def start(self):
        while True:
            for current in self.get_nodes():
                if current[1]["MODE"] == "ROUTER":
                    if len(self.transmitionQueues[current[0]].items) > 0:
                        request = yield self.transmitionQueues[current[0]].get()
                        if request.destinationNode == 'NA':
                            self.choose_request_destination(current[0],request)
                        next = self.next_hop(current[0],request.destinationNode)
                        delay = request.get_transmition_delay(current[0],next,self)
                        # # ##print("link ", neighbor[0], "-", current[0], " transmition delay is ", delay)
                        start_delayed(self.env ,self.transmit_request(request=request, sender=current[0], reciever=next), delay)
                if current[1]["MODE"] == "COMPUTE" or current[1]["MODE"] == "CLOUD":
                    if len(self.transmitionQueues[current[0]].items) > 0:
                        request = yield self.transmitionQueues[current[0]].get()
                        if request.destinationNode == 'NA':
                            self.choose_request_destination(current[0],request)
                        if request.destinationNode != current[0]:
                            next = self.next_hop(current[0],request.destinationNode)
                            delay = request.get_transmition_delay(current[0],next,self)
                            # # ##print("next -------<", next)
                            start_delayed(self.env ,self.transmit_request(request=request, sender=current[0], reciever=next), delay)
                        else:
                            self.internalQueues[current[0]].put(request)
                            start_delayed(self.env ,self.recieve_internal_request(current[0],request), 0.0000001)

                if current[1]["MODE"] == "ZONE":
                    if len(self.transmitionQueues[current[0]].items) > 0:
                        request = yield self.transmitionQueues[current[0]].get()
                        if request.destinationNode == 'NA':
                            self.choose_request_destination(current[0],request)
                        next = self.next_hop(current[0],request.destinationNode)
                        self.send_request(request=request, sender=current[0], reciever=next)   
                for neighbor in self.get_neighbors(current[0]):
                    if len(self.linkStores[neighbor+'-'+str(current[0])].items) > 0:
                        delay = self.get_link_propagation_delay(neighbor,current[0])
                        # # ##print("link ", neighbor[0], "-", current[0], " propagation delay is ", delay)
                        yield start_delayed(self.env ,self.recieve_request(sender=neighbor,reciever=current[0]), delay)

            
            self.env.step()

    def next_hop(self, current, target):
        target = str(target)
        current = str(current)
        # # ##print("current", current)
        # # #print(self.routingTable[current])
        # # ##print("nexthop", self.routingTable[current][target][0][1])
        return self.routingTable[current][target][0][1]
                                
    
    def send_request(self, sender, reciever, request):
        """
        Simulates sending a request form a zone
        """
        ##print("Packet ", request.id, " Sent to ", reciever, " from ", sender, " at ", str(self.env.now))
        self.linkStores[str(sender)+'-'+str(reciever)].put(request)

    def create_routing_table(self):
        dijkstra_paths = nx.all_pairs_dijkstra_path(G=self.G, weight=self.compute_distance_between_two_nodes)
        allNodes = self.get_nodes()
        for path in dijkstra_paths:
            source = path[0]
            for key in path[1].keys():
                self.routingTable[str(source)][str(key)][0] = path[1][key]
        for source in allNodes:
            for target in allNodes:
                all_paths = nx.all_simple_paths(G=self.G, source=source[0], target=target[0])
                index = 1
                tmp = []
                for path in all_paths: 
                    tmp.append(path)
                tmp.sort(key = len)
                for path in tmp:
                    if path not in self.routingTable[str(source[0])][str(target[0])].values():
                        self.routingTable[str(source[0])][str(target[0])][index] = path
                        index += 1
        

    def get_all_shortests_paths_routes(self):
        """
        Retruns:
            returns a dictionary of all shortest paths routes between nodes using Djikstra algorithm
        """
        shortestPathRouteData = nx.all_pairs_dijkstra_path(G=self.G, weight=self.compute_distance_between_two_nodes)
        dataDict = dict()
        for data in shortestPathRouteData:
            dataDict[data[0]] = dict()
            dataDict[data[0]] = data[1]
        return dataDict

    def get_path_cost(self, source, target):
        """
        Args:
            source (str): source node id
            target (str): destination node id
        Retruns:
            returns path cost based on distance between them
        """
        shortestPathData = self.get_all_shortest_path_distance()
        return shortestPathData[source][target]

    def get_all_shortest_paths(self, save, jsonFile):
        """
        Args:
            source (str): source node id
            target (str): destination node id
        Retruns:
            returns path cost based on bandwidth between them
        """
        def save(jsonFile, shortestPathData):
            with open(jsonFile, 'w') as file:
                js.dump(shortestPathData, file, indent=4)
        # # #print(self.get_all_shortest_path_distance())
        shortestCostData = self.get_all_shortest_path_distance()
        shortestPathRouteData = self.get_all_shortests_paths_routes()

        dataDict = defaultdict(lambda : defaultdict(dict))
        
        for source in self.get_nodes():
            for target in self.get_nodes():
                # # #print(shortestCostData[source][target])
                dataDict[source[0]][target[0]]['COST'] = shortestCostData[source[0]][target[0]]
                dataDict[source[0]][target[0]]['route'] = shortestPathRouteData[source[0]][target[0]]

        if save:
            save(jsonFile,dataDict)
        # # #print(shortestPathRouteData)
        return dataDict

    def get_nodes_att(self):
        """
        Returns:
            A dictionary with the features of the nodes
        """
        return self.nodeAttributes

    def save_network_png(self, pngFile):
        """
        Args:
            pngFile (str): the path in which the plot is saved
        Returns:
            saves the network topology as a png file
        """
        elarge = [(u, v) for (u, v, d) in self.G.edges(data=True) if d["bandwidth"] > self.MEDIAN_BW]
        esmall = [(u, v) for (u, v, d) in self.G.edges(data=True) if d["bandwidth"] <= self.MEDIAN_BW]

        pos = nx.spring_layout(self.G, seed=7)  # positions for all nodes - seed for reproducibility
        nodesPosX = nx.get_node_attributes(self.G, 'X')
        nodesPosY = nx.get_node_attributes(self.G, 'Y')
        for node in nodesPosX:
            nodesPosY[node] = [nodesPosX[node], nodesPosY[node]]
        # # #print(nodesPosY)
        # nodes
        nx.draw_networkx_nodes(self.G, nodesPosY, node_size=400)

        # edges
        nx.draw_networkx_edges(self.G, nodesPosY, edgelist=elarge, width=6)
        nx.draw_networkx_edges(
            self.G, nodesPosY, edgelist=esmall, width=6, alpha=0.5, edge_color="b", style="dashed"
        )

        # node labels
        nx.draw_networkx_labels(self.G, nodesPosY, font_size=15, font_family="sans-serif")
        # edge bandwidth labels
        edge_labels = nx.get_edge_attributes(self.G, "bandwidth")
        nx.draw_networkx_edge_labels(self.G, nodesPosY, edge_labels)
        ax = plt.gca()
        ax.margins(0.08)
        plt.axis("off")
        plt.tight_layout()
        # nx.draw(self.G)
        # cyjsGraph = nx.cytoscape_data(G)
        # with open(graphAddress, 'w') as file:
            # js.dump(cyjsGraph,file, indent=4)
        plt.savefig(pngFile)

    def __str__(self):
        """
        Returns:
            #prints the graph as a string
        """
        print(self.G.edges)
        for node in self.G.nodes:
            print("Node :", node)
        for edge in self.G.edges(data=True):
            print("Edge: ", edge)
            
    def load_cyjs(self,jsonFile):
        """
        Args:
            jsonFile (str): the path in which the network definiation is saved
        Returns:
            Loads the graph from json formatted definition
        """
        with open(jsonFile, 'r') as file:
            networkData = file.read()
            networkDataJson = js.loads(networkData)
            self.G = nx.cytoscape_graph(networkDataJson)
            
    def save_cyjs(self,jsonFile):
        """
        Args:
            jsonFile (str): the path in which the network definiation is going to saved
        Returns:
            Saves the current graph of the network as a json file
        """
        with open(jsonFile, 'w') as file:
            networkDataJson = nx.cytoscape_data(self.G)
            js.dump(networkDataJson, file, indent=4)

    def return_bandwidth(self, source, target, edge):
        """
        Args:
            source (str): source node id
            target (str): destination node id
        Returns:
            The bandwidth of an specified link
        """
        return edge['bandwidth']

    def get_link_bitrate(self, source, target):
        """
        Args:
            source (str): source node id
            target (str): destination node id
        Returns:
            The bitrate of an specified link
        """
        for link in self.get_links():
            if (str(link[0]) == str(source) and str(link[1]) == str(target)) or (str(link[0]) == str(target) and str(link[1]) == str(source)):
                # # #print(link)
                return self.calculate_bitrate(link)
    
    def calculate_bitrate(self, edge):
        """
        Args:
            edge (edge): link between to nodes
        Returns:
            The bitrate of an specified link
        """
        return edge[2]['bandwidth']*np.log(1 + edge[2]['SNR'])

    def get_all_shortest_path_distance(self):
        """
        Returns:
            A dictionary of shortest paths between nodes
        """
        shortestPathData = nx.shortest_path_length(G=self.G, weight=self.compute_distance_between_two_nodes, method='dijkstra')
        dataDict = dict()
        for data in shortestPathData:
            dataDict[data[0]] = dict()
            dataDict[data[0]] = data[1]
        return dataDict
        
    #===============================================================
    # Links
    # / These are link related functions
    #===============================================================

class Request:
    def __init__(self, name , source, destinationService, size, instructions, cpu, ram, sub, issuedBy, masterService,masterRequest, env, logger=None):
        self.id = uuid.uuid4().hex
        self.size = size
        self.source = source
        self.name = name
        self.destinationNode = 'NA'
        self.destinationService = destinationService
        self.ram = ram
        self.cpu = cpu
        self.instructions = instructions
        self.issueTime = 0
        self.responseTime = 0
        self.logger = logger or logging.getLogger(__name__) 
        self.response = False
        self.failed = 0
        self.satisfied = 0
        self.sub = sub
        self.issuedBy = issuedBy
        self.masterService = masterService
        self.masterRequest = masterRequest
        self.history = []
        self.latency = 0


    def get_transmition_delay(self, source, destination, topology):
        # return topology.get_link_bitrate(source, destination)
        # # #print(source, destination)
        # # #print(destination)
        return (self.size / topology.get_link_bitrate(source, destination))
    
    def set_destination_node(self, destinationNode):
        self.destinationNode = destinationNode