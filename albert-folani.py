from network import Topology as TP
from network import Request as rq
from functools import partial, wraps
import json as js
# from Topology import return_weight
import random as rnd
import matplotlib.pyplot as plt
import networkx as nx



if __name__ == "__main__":
    # graph = nx.barabasi_albert_graph(10, 2, 0, initial_graph=None)
    with open('./folani.json', 'r') as file:
        networkData = file.read()
        networkDataJson = js.loads(networkData)
        graph = nx.cytoscape_graph(networkDataJson)
        # networkDataJson = nx.cytoscape_data(graph)
        # js.dump(networkDataJson, file, indent=4)


        # elarge = [(u, v) for (u, v, d) in graph.edges(data=True) if d["bandwidth"] > self.MEDIAN_BW]
        # esmall = [(u, v) for (u, v, d) in graph.edges(data=True) if d["bandwidth"] <= self.MEDIAN_BW]
        elarge = 10
        esmall = 10
        pos = nx.circular_layout(G=graph, scale=300000, center=None, dim=2)

        for i in range(10):
            for node in networkDataJson['elements']['nodes']:
                # print(type(node['data']['id']))
                if int(node['data']['id']) == i:
                    node['data']['X'] = pos[i][0]
                    node['data']['Y'] = pos[i][1]
        print(networkDataJson)
        with open('./tst.json', 'w') as f:
            js.dump(networkDataJson, f, indent=4)
        # pos = nx.planar_layout(G=graph, scale=10, center=None, dim=2)  # positions for all nodes - seed for reproducibility
        # nodesPosX = nx.get_node_attributes(graph, 'X')
        # nodesPosY = nx.get_node_attributes(graph, 'Y')
        # for node in nodesPosX:
        #     nodesPosY[node] = [nodesPosX[node], nodesPosY[node]]

        # pos = nx.spring_layout(G)
        # print(nodesPosY)
        # nodes
        nx.draw_networkx_nodes(graph, pos, node_size=600)

        # edges
        nx.draw_networkx_edges(graph, pos, edgelist=graph.edges, width=6)

        # node labels
        nx.draw_networkx_labels(graph, pos, font_size=20, font_family="sans-serif")
        # edge bandwidth labels
        edge_labels = nx.get_edge_attributes(graph, "bandwidth")
        nx.draw_networkx_edge_labels(graph, pos, edge_labels)
        ax = plt.gca()
        ax.margins(0.08)
        plt.axis("off")
        plt.tight_layout()
        # nx.draw(graph)
        # cyjsGraph = nx.cytoscape_data(G)
        # with open(graphAddress, 'w') as file:
            # js.dump(cyjsGraph,file, indent=4)
        plt.savefig('./folani.png')
