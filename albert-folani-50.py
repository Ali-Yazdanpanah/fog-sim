from network import Topology as TP
from network import Request as rq
from functools import partial, wraps
import json as js
# from Topology import return_weight
import random
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np



if __name__ == "__main__":
        graph = nx.barabasi_albert_graph(54, 1, seed=None, initial_graph=None)
        networkDataJson = nx.cytoscape_data(graph)
        cloud = {'data': {'id': 'CLOUD', 'value': 'CLOUD', 'name': 'CLOUD', 'X': 4500, 'Y': 4500, "RAM":9999999999999, "CPU":9999999, "IPS": 288000000, "MODE": 'CLOUD'}}
        networkDataJson['elements']['nodes'].append(cloud)
        data = nx.cytoscape_graph(networkDataJson)
        d = dict(data.degree)
        leaves = [x for x in data.nodes() if d[x] <= 1] 
        SCALE = 5000
        NUM_ZONES = 4
        NUM_CLOUD_NEIGHBORS = 4
        CURRENT_ZONES = 0
        # fig, ax = plt.subplots()
        # elarge = [(u, v) for (u, v, d) in graph.edges(data=True) if d["bandwidth"] > self.MEDIAN_BW]
        # esmall = [(u, v) for (u, v, d) in graph.edges(data=True) if d["bandwidth"] <= self.MEDIAN_BW]
        RED = '#9B2242'
        GREEN = '#026C7C'
        BLUE = '#01172F'
        elarge = 1
        esmall = 1

        pos = nx.spring_layout(G=data)
        scaled_pos = nx.rescale_layout_dict(pos, scale=SCALE)
        zones = random.sample(leaves, k=NUM_ZONES)
        CLOUD_NEIGHBOR_CANDIDATES = [x for x in leaves if x not in zones and x != 'CLOUD']
        CLOUD_NEIGHBORS = random.sample(CLOUD_NEIGHBOR_CANDIDATES, k=NUM_CLOUD_NEIGHBORS)
        for node in CLOUD_NEIGHBORS:
            networkDataJson['elements']['edges'].append({
                "data": {
                    "source": 'CLOUD',
                    "target": node,
                    "PS": 300000000,
                    "COST": 20,
                    "SNR": 50,
                    "bandwidth": 200000
                }
            })
        data = nx.cytoscape_graph(networkDataJson)
        color_map = []
        size_map = []
        for node in networkDataJson['elements']['nodes']:
            # print(node)
            try:
                index = (int(node['data']["id"]))
            except:
                index = node['data']["id"]
            if index not in zones and index != 'CLOUD':
                node['data']['X'] = scaled_pos[index][0]
                node['data']['Y'] = scaled_pos[index][1]
                node['data']['RAM'] = 8000
                node['data']['CPU'] = 8
                node['data']['IPS'] = 10000
                node['data']['MODE'] = 'COMPUTE' 
                size_map.append(700)
                color_map.append(RED)
            elif index == 'CLOUD':
                size_map.append(2000)
                color_map.append(BLUE)   
            else:
                node['data']['X'] = scaled_pos[index][0]
                node['data']['Y'] = scaled_pos[index][1]
                node['data']['MODE'] = 'ZONE' 
                size_map.append(700)
                color_map.append(GREEN)      
        for link in networkDataJson['elements']['edges']:
            link['data']['PS'] = 300000000
            link['data']['COST'] = 1
            link['data']['SNR'] = 30
            link['data']['bandwidth'] = 25000

        # pos = nx.planar_layout(G=graph, scale=10, center=None, dim=2)  # positions for all nodes - seed for reproducibility
        nodesPosX = nx.get_node_attributes(data, 'X')
        nodesPosY = nx.get_node_attributes(data, 'Y')
        nodePos = nodesPosY
        for node in nodesPosX:
            nodePos[node] = [nodesPosX[node], nodesPosY[node]]

        # print(nodesPosY)
        pos = nx.spring_layout(data)
        fig, ax = plt.subplots(figsize=(2^16, 2^16))
        plt.title('Fog node locations')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.xlim(-1.1*SCALE, SCALE*1.1)
        plt.ylim(-1.1*SCALE, SCALE*1.1)
        # ax.margins(0.0008)
        # print(nodesPosY)
        # nodes
        nx.draw(data, pos=scaled_pos, node_size=size_map, node_color=color_map, ax=ax, with_labels = True, font_color="whitesmoke")

        # # edges
        # nx.draw_networkx_edges(data, pos=pos, edgelist=data.edges, width=1)

        # node labels
        # nx.draw_networkx_labels(data, pos, font_size=2, font_family="sans-serif")
        # edge bandwidth labels
        # edge_labels = nx.get_edge_attributes(data, "bandwidth")
        # nx.draw_networkx_edge_labels(data, pos)
        ax.set_axis_on()
        ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
        red_patch = mpatches.Patch(color=RED, label='COMPUTE NODE')
        green_patch = mpatches.Patch(color=GREEN, label='REQUEST ZONE')
        blue_patch = mpatches.Patch(color=BLUE, label='CLOUD')
        plt.legend(handles=[red_patch,green_patch,blue_patch])
        plt.tight_layout()
        # nx.draw(data)
        # cyjsGraph = nx.cytoscape_data(G)
        with open('./graphs/50node.json', 'w+') as file:
            js.dump(networkDataJson,file, indent=4)
        plt.savefig('./graphs/50.svg')
