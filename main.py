from network import Topology as TP
from network import Packet as pk
# from Topology import return_weight

import simpy
import matplotlib.pyplot as plt
import networkx as nx

if __name__ == "__main__":
    
    env = simpy.Environment()    
    myTP = TP()
    myTP.load_cyjs('./test_graph.json')

    testPacket = pk('testUser','1', 10240)
    # print("Packet delivery time for packet from a to b is: " + str(myTP.get_packet_delivery_time('b','a',testPacket)) + " Seconds")
    

    myTP.save_network_png('./test.png')
    env.process(myTP.get_packet_delivery_time('d','c',testPacket,env))
    env.run(until=150)
    # print("Propgation time of d to c is: " + str(myTP.get_packet_delivery_time('d','c')))
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
