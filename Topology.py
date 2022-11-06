import logging

import json as js
import networkx as nx
import matplotlib.pyplot as plt

from networkx.readwrite import json_graph
from collections import defaultdict


class Topology:
    """
    This class unifies the functions to deal with **Complex Networks** as a network topology within of the simulator. In addition, it facilitates its creation, and assignment of attributes.
    """

    LINK_BW = "BW"
    "Link feature: Bandwidth"

    LINK_PR = "PR"
    "Link feauture:  Propagation delay"

    # LINK_LATENCY = "LATENCY"
    # " A edge or a network link has a Bandwidth"

    NODE_IPT = "IPT"
    "Node feature: IPS . Instructions per Simulation Time "
    
    def __init__(self, logger=None):
        # G is a nx.networkx graph
        self.G = None
        self.nodeAttributes = {}
        self.logger = logger or logging.getLogger(__name__)


    def get_edges(self):
        """
        Returns:
            list: a list of graph edges, i.e.: ((1,0),(0,2),...)
        """
        return self.G.edges


    def get_nodes(self):
        """
        Returns:
            list: a list of graph nodes
        """
        return self.G.nodes

    def save_network_png(self, pngFile):

        elarge = [(u, v) for (u, v, d) in self.G.edges(data=True) if d["weight"] > 0.5]
        esmall = [(u, v) for (u, v, d) in self.G.edges(data=True) if d["weight"] <= 0.5]

        pos = nx.spring_layout(self.G, seed=7)  # positions for all nodes - seed for reproducibility

        # nodes
        nx.draw_networkx_nodes(self.G, pos, node_size=700)

        # edges
        nx.draw_networkx_edges(self.G, pos, edgelist=elarge, width=6)
        nx.draw_networkx_edges(
            self.G, pos, edgelist=esmall, width=6, alpha=0.5, edge_color="b", style="dashed"
        )

        # node labels
        nx.draw_networkx_labels(self.G, pos, font_size=20, font_family="sans-serif")
        # edge weight labels
        edge_labels = nx.get_edge_attributes(self.G, "weight")
        nx.draw_networkx_edge_labels(self.G, pos, edge_labels)
        ax = plt.gca()
        ax.margins(0.08)
        plt.axis("off")
        plt.tight_layout()
        # nx.draw(self.G)
        # cyjsGraph = nx.cytoscape_data(G)
        # with open(graphAddress, 'w') as file:
            # js.dump(cyjsGraph,file, indent=4)
        plt.savefig(pngFile)


    def print_graph(self):
        print(self.G.edges)
        for node in self.G.nodes:
            print("Node :", node)
        for edge in self.G.edges(data=True):
            print("Edge: ", edge)
            
    def load_cyjs(self,jsonFile):
        with open(jsonFile, 'r') as file:
            networkData = file.read()
            networkDataJson = js.loads(networkData)
            self.G = nx.cytoscape_graph(networkDataJson)
            
            # TODO
            # print(self.G)
            # for edge in networkDataJson['elements']['edges']:
            #     self.G.add_edge(edge['source'], edge['target'], BW=edge[self.LINK_BW],PR=edge[self.LINK_PR])

    def dump_cyjs(self,jsonFile):
        with open(jsonFile, 'w') as file:
            networkDataJson = nx.cytoscape_data(self.G)
            js.dump(networkDataJson, file, indent=4)
        
    def get_edges(self):
        return self.G.edges(data=True)

    def get_edge(self, source, target):
        """
        Args:
            key (str): a edge identifier, i.e. (1,9)
        Returns:
            list: a list of edge attributes
        """
        allEdges = self.get_edges()
        for edge in allEdges:
            if edge[0] == source and edge[1] == target:
                return edge
    

    def get_edge_weight(self, source, target, Edges):
        for edge in Edges:
            if edge[0] == source and edge[1] == target:
                return edge[2]['weight']

    def return_weight(self, source, target, edge):
        return edge['weight']

    def all_shortest_path_weight(self):
        shortestPathData = nx.shortest_path_length(G=self.G, weight=self.return_weight, method='dijkstra')
        dataDict = dict()
        for data in shortestPathData:
            dataDict[data[0]] = dict()
            dataDict[data[0]] = data[1]
        return dataDict
        
    def get_all_shortests_paths_routes(self):
        shortestPathRouteData = nx.all_pairs_dijkstra_path(G=self.G, weight=self.return_weight)
        dataDict = dict()
        for data in shortestPathRouteData:
            dataDict[data[0]] = dict()
            dataDict[data[0]] = data[1]
        return dataDict

    def get_path_cost(self, source, target):
        shortestPathData = self.all_shortest_path_weight()
        return shortestPathData[source][target]

    def get_all_shortest_paths(self, save, jsonFile):
        def save(jsonFile, shortestPathData):
            with open(jsonFile, 'w') as file:
                js.dump(shortestPathData, file, indent=4)
        shortestPathWeightData = self.all_shortest_path_weight()
        shortestPathRouteData = self.get_all_shortests_paths_routes()

        dataDict = defaultdict(lambda : defaultdict(dict))
        
        for source in self.get_nodes():
            for target in self.get_nodes():
                dataDict[source][target]['cost'] = shortestPathWeightData[source][target]
                dataDict[source][target]['route'] = shortestPathRouteData[source][target]

        if save:
            save(jsonFile,dataDict)
        print(shortestPathRouteData)
        return dataDict



    

    # def create_random_topology(self, nxGraphGenerator, params):
    #     """
    #     It generates the topology from a Graph generators of NetworkX
    #     Args:
    #          nxGraphGenerator (function): a graph generator function
    #     Kwargs:
    #         params (dict): a list of parameters of *nxGraphGenerator* function
    #     """
    #     try:
    #         self.G = nxGraphGenerator(*params)
    #     except:
    #         raise Exception