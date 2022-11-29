#===============================================================
# Network
# / This file is responsible for modeling the network
#===============================================================



import time

import logging
import math

import json as js
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import simpy
from simpy.util import start_delayed


from simpy.resources.store import Store
from simpy.resources.store import FilterStore
from networkx.readwrite import json_graph
from collections import defaultdict
from util import AutoVivification
#===============================================================
# Topology
# / This class is responsible for modeling network topology
#===============================================================


class Service:
    
    def __init__(self, name, place, ram, cpu, needs):
        self.name = name
        self.place = place
        self.ram = ram
        self.cpu = cpu
        self.needs = needs
        self.serviceStore = simpy.FilterStore(self.env)
    





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
        self.until = 0
        self.nodeAttributes = {}
        self.linkStores = {}
        self.nodeStores = {}
        self.remainingMEM = {}
        self.remainingCPU = {}
        self.nodeServiceStores = {}
        self.transmitionQueues = {}
        self.recievedRequests = {}
        self.routingTable = AutoVivification()
        self.logger = logger or logging.getLogger(__name__)
        self.env = env
        self.placementTable = AutoVivification()
        jsonFile = kwargs.get('jsonFile', None)
        if jsonFile is not None:
            self.load_cyjs(jsonFile)
        for link in self.get_links():
            self.linkStores[link[0]+'-'+link[1]] = simpy.Store(self.env)
            self.linkStores[link[1]+'-'+link[0]] = simpy.Store(self.env)
        for node in self.get_nodes():
            self.nodeStores[node[0]] = simpy.FilterStore(self.env)
            self.recievedRequests[node[0]] = simpy.Store(self.env)
            self.transmitionQueues[node[0]] = simpy.Store(self.env)
            if node[1]['MODE'] == 'COMPUTE':
                self.nodeServiceStores[node[0]] = simpy.FilterStore(self.env)
                self.remainingMEM[node[0]] = node[1]['RAM']
                self.remainingCPU[node[0]] = node[1]['CPU']


    #===============================================================
    # service
    # / These are service placement related functions
    #===============================================================

    def get_all_service_nodes(self, serviceName):
        print(self.placementTable)
        print({k: v for k, v in self.placementTable[serviceName]['deployments'] if v[1] > 0})
        return {k: v for k, v in self.placementTable[serviceName]['deployments'] if v[1] > 0}
        
    def set_request_destination_node(self, nodeID, request):
        current = self.get_node(nodeID)
        for item in self.nodeServiceStores[current].items:
            if item.name == request.destinationService:
                return request.set_destination_node(nodeID)
        else:
            for node in self.get_neighbors(current):
                pass

    def create_service_placement_table(self, services):
        for service in services:
            self.placementTable[service[0]] = service[1] 
        # print(self.placementTable)
        print({k: v for k, v in self.placementTable['front']['deployments'] if v[1] > 0})
        yield self.env.timeout(0)
        # print(self.get_all_service_nodes['front'])
        


    def place_services(self,placementTable):
        for node in self.get_nodes():
            for service in placementTable.keys():
                index = 0
                for index in range(placementTable[service]['deployments'][node[0]]['replicas']):
                    service = Service(node[0],placementTable[service]['RAM'],placementTable[service]['CPU'],placementTable[service]['needs'])
                    self.nodeServiceStores[node[0]].put(services)


    #===============================================================
    # Node
    # / These are node related functions
    #===============================================================

    def get_node(self, id):
        """
        Returns:
            node: get a graph node
        """
        for node in self.G.nodes(data=True):
            if node[0] == id:
                return node

    def get_nodes(self):
        """
        Returns:
            list: a list of graph nodes
        """
        return self.G.nodes(data=True)

    def get_neighbors(self, nodeID):
        return self.G.neighbors(nodeID)


    def get_compute_nodes(self):
        """
        Returns:
            list: a list of compute nodes
        """
        return [node for node in self.get_nodes(data=True) if node[1]['MODE'] == 'COMPUTE']

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
            if node[0] == source or node[0] == target:
                nodes.append(node[1])
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
            if (link[0] == source and link[1] == target) or (link[0] == target and link[1] == source):
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
            if (link[0] == source and link[1] == target) or (link[0] == target and link[1] == source):
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
            if (link[0] == source and link[1] == target) or (link[0] == target and link[1] == source):
                return link[2]['PS']


    def get_link_bitrates(self):
        """
        Returns:
            returns all link bitrates
        """
        return [(link[0],link[1], self.calculate_bitrate(link)) for link in self.get_links()]

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
        delay = time - self.env.now 
        # print(delay)
        if delay == 0:
            yield self.put_request_in_ts_queue(current[0], request) 
        else:
            yield start_delayed(self.env ,self.put_request_in_ts_queue(current[0], request), delay)

    
    def put_request_in_ts_queue(self, current, request):
        print("Putting request ", request.name ," on transmition queue in node ", current, " at ", str(self.env.now))
        for node in self.get_nodes():
            if node[0] == current:
                yield self.transmitionQueues[node[0]].put(request)


    def start_request_process(self, request, nodeID):
        node = self.get_node(nodeID)
        requestExecutionTime = (request.instructions / (node[1]['IPS'])*1.000)
        self.remainingCPU[nodeID] = self.remainingCPU[nodeID] - request.cpu
        self.remainingMEM[nodeID] = self.remainingMEM[nodeID] - request.ram
        start_delayed(self.env ,self.finish_request(request=request, nodeID=nodeID), requestExecutionTime)

    def finish_request(self, request, nodeID):
        print("request ", request.name ," finished on node: ", nodeID, " at ", self.env.now)
        self.remainingCPU[nodeID] = self.remainingCPU[nodeID] + request.cpu
        self.remainingMEM[nodeID] = self.remainingMEM[nodeID] + request.ram
        yield self.nodeStores[nodeID].get(filter=lambda request: True)

    def recieve_request(self, sender, reciever):
        # yield self.env.timeout(delay)
        request = yield self.linkStores[sender+'-'+reciever].get()    
        if request.destinationNode == reciever:
            print("Packet ", request.name, " reached destination ", reciever, " at ", str(self.env.now))
            self.start_request_process(request, reciever)   
            yield self.nodeStores[reciever].put(request)
        else:
            print("Packet ", request.name, " recieved at", reciever, "...puting in queue at", str(self.env.now))
            yield self.transmitionQueues[reciever].put(request) 

    def transmit_request(self, request, sender, reciever):
        # yield self.env.timeout(delay)
        print("Packet ", request.name, " transmited to ", reciever, " from ", sender, " at ", str(self.env.now))
        yield self.linkStores[sender+'-'+reciever].put(request)
        

    def transimition_loop(self):
        while True:
            for current in self.get_nodes():
                if len(self.transmitionQueues[current[0]].items) > 0:
                    request = yield self.transmitionQueues[current[0]].get()
                    next = self.next_hop(current[0],request.destinationNode)
                    delay = request.get_transmition_delay(current[0],next,self)
                    print("link ", neighbor[0], "-", current[0], " transmition delay is ", delay)
                    start_delayed(self.env ,self.transmit_request(request=request, sender=current[0], reciever=next), delay)


    def process_recieved_requests_loop(self):
        while True:
            for current in self.get_nodes():
                for neighbor in self.get_neighbors(current[0]):
                    if len(self.linkStores[neighbor[0]+'-'+current[0]].items) > 0:
                        delay = self.get_link_propagation_delay(neighbor[0],current[0])
                        print("link ", neighbor[0], "-", current[0], " propagation delay is ", delay)
                        start_delayed(self.env ,self.recieve_request(sender=neighbor[0],reciever=current[0]), delay)
            

    def start(self):
        while True:
            for current in self.get_nodes():
                if len(self.transmitionQueues[current[0]].items) > 0:
                    request = yield self.transmitionQueues[current[0]].get()
                    next = self.next_hop(current[0],request.destinationNode)
                    delay = request.get_transmition_delay(current[0],next,self)
                    # print("link ", neighbor[0], "-", current[0], " transmition delay is ", delay)
                    start_delayed(self.env ,self.transmit_request(request=request, sender=current[0], reciever=next), delay)
                for neighbor in self.get_neighbors(current[0]):
                    if len(self.linkStores[neighbor[0]+'-'+current[0]].items) > 0:
                        delay = self.get_link_propagation_delay(neighbor[0],current[0])
                        # print("link ", neighbor[0], "-", current[0], " propagation delay is ", delay)
                        yield start_delayed(self.env ,self.recieve_request(sender=neighbor[0],reciever=current[0]), delay)
            self.env.step()

    def next_hop(self, current, target):
        return self.routingTable[current][target][0][1]


                                            
    
    # def send_request(self, source, target, request, env):
    #     """
    #     Simulates sending a request
    #     """
    #     time = self.get_request_delivery_time(source, target, request)
    #     yield env.timeout(time)


    def create_routing_table(self):
        dijkstra_paths = nx.all_pairs_dijkstra_path(G=self.G, weight=self.compute_distance_between_two_nodes)
        allNodes = self.get_nodes()
        for path in dijkstra_paths:
            source = path[0]
            for key in path[1].keys():
                self.routingTable[source][key][0] = path[1][key]
        for source in allNodes:
            for target in allNodes:
                all_paths = nx.all_simple_paths(G=self.G, source=source[0], target=target[0])
                index = 1
                tmp = []
                for path in all_paths: 
                    tmp.append(path)
                tmp.sort(key = len)
                for path in tmp:
                    if path not in self.routingTable[source[0]][target[0]].values():
                        self.routingTable[source[0]][target[0]][index] = path
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
        # print(self.get_all_shortest_path_distance())
        shortestCostData = self.get_all_shortest_path_distance()
        shortestPathRouteData = self.get_all_shortests_paths_routes()

        dataDict = defaultdict(lambda : defaultdict(dict))
        
        for source in self.get_nodes():
            for target in self.get_nodes():
                # print(shortestCostData[source][target])
                dataDict[source[0]][target[0]]['cost'] = shortestCostData[source[0]][target[0]]
                dataDict[source[0]][target[0]]['route'] = shortestPathRouteData[source[0]][target[0]]

        if save:
            save(jsonFile,dataDict)
        # print(shortestPathRouteData)
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
        # print(nodesPosY)
        # nodes
        nx.draw_networkx_nodes(self.G, nodesPosY, node_size=600)

        # edges
        nx.draw_networkx_edges(self.G, nodesPosY, edgelist=elarge, width=6)
        nx.draw_networkx_edges(
            self.G, nodesPosY, edgelist=esmall, width=6, alpha=0.5, edge_color="b", style="dashed"
        )

        # node labels
        nx.draw_networkx_labels(self.G, nodesPosY, font_size=20, font_family="sans-serif")
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
            Prints the graph as a string
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
            if (link[0] == source and link[1] == target) or (link[0] == target and link[1] == source):
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
    def __init__(self, name , source, destinationService, destinationNode, size, instructions, ram, cpu, logger=None):
        self.size = size
        self.source = source
        self.name = name
        self.destinationNode = destinationNode
        self.destinationService = destinationService
        self.ram = ram
        self.cpu = cpu
        self.instructions = instructions
        self.Time = time.time()
        self.logger = logger or logging.getLogger(__name__) 

    def get_transmition_delay(self, source, destination, topology):
        # return topology.get_link_bitrate(source, destination)
        return (self.size / topology.get_link_bitrate(source, destination))
    
    def set_destination_node(self, destinationNode):
        self.destinationNode = destinationNode