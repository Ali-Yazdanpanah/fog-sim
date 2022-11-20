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

from networkx.readwrite import json_graph
from collections import defaultdict


#===============================================================
# Topology
# / This class is responsible for modeling network topology
#===============================================================

class Topology:
    """
    This class unifies the functions to deal with **Complex Networks** as a network topology within of the simulator. In addition, it facilitates its creation.
    """

    # LINK_LATENCY = "LATENCY"
    # " A edge or a network link has a Bandwidth"

    MEDIAN_BW = 1500

    SNR = 30

    def __init__(self, logger=None):
        # G is a nx.networkx graph
        self.G = None
        self.nodeAttributes = {}
        self.logger = logger or logging.getLogger(__name__)

    #===============================================================
    # Node
    # / These are node related functions
    #===============================================================

    def get_nodes(self):
        """
        Returns:
            list: a list of graph nodes
        """
        return self.G.nodes(data=True)

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

    def get_link_propagation_time(self, source, target):
        """
        Args:
            source (str): source node id
            target (str): destination node id
        Returns:
            returns the propagation time of the specified link using source and destination target
        """
        return self.compute_distance_between_two_nodes(source, target, _t=None) / self.get_link_propagation_speed(source, target)

    def get_packet_delivery_time(self, source, target, packet):
        """
        Args:
            source (str): source node id
            target (str): destination node id
            packet (packet): packet object
        Returns:
            returns the delievery time of the specified packet on the specified link using source and destination target
        """
        return self.get_link_propagation_time(source, target) + packet.calculate_transmition_time(source,target,self)


    def send_packet(self, source, target, packet, env):
        """
        Simulates sending a packet
        """
        time = self.get_packet_delivery_time(source, target, packet)
        yield env.timeout(time)


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
        

class Packet:
    def __init__(self, source, destination, size, logger=None):
        self.size = size
        self.source = source
        self.destination = destination
        self.Time = time.time()
        self.logger = logger or logging.getLogger(__name__) 

    def calculate_transmition_time(self, source, destination, topology):
        # return topology.get_link_bitrate(source, destination)
        return (self.size / topology.get_link_bitrate(source, destination))
           
