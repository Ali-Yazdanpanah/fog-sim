from network import Topology as TP
from network import Packet as pk
# from Topology import return_weight

import matplotlib.pyplot as plt
import networkx as nx

if __name__ == "__main__":
    
    
    myTP = TP()
    myTP.load_cyjs('./test_graph.json')

    # testPacket = pk('testUser','1', 2048)
    # print("Transmition time for packet from a to b is: " + str(testPacket.calculate_transmition_time('b','a',myTP)) + " Seconds")
    

    myTP.save_network_png('./test.png')
    print(myTP.get_distance('d','c'))
    # edges = myTP.get_edges()
    # print(myTP.get_links())
    # print(myTP.get_routers())
    # graph = myTP.G.edges
    # print(myTP.get_link_bitrates())
    # print(('a','b',graph))
    # myTP.get_all_shortest_paths(save=True, jsonFile='./shortest_path.json')
    # myTP.all_shortest_path_weight()
    # myTP.print_graph()
    # myTP.dump_cyjs(jsonFile='dump.json')
