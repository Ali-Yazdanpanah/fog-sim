from Topology import Topology as TP
# from Topology import return_weight

import matplotlib.pyplot as plt
import networkx as nx

if __name__ == "__main__":
    myTP = TP()
    myTP.load_cyjs('./test_graph.json')
    myTP.save_network_png('./test.png')
    edges = myTP.get_edges()
    nodes = myTP.get_nodes()
    graph = myTP.G.edges
    # print(nodes)
    # print(('a','b',graph))
    # print(myTP.get_edge_weight('a','b',myTP.get_edges()))
    myTP.get_all_shortest_paths(save=True, jsonFile='./shortest_path.json')
    # myTP.all_shortest_path_weight()
    # myTP.print_graph()
    # myTP.dump_cyjs(jsonFile='dump.json')
