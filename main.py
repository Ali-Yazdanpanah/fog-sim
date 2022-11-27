from network import Topology as TP
from network import Packet as pk
from functools import partial, wraps
# from Topology import return_weight

import simpy
import matplotlib.pyplot as plt
import networkx as nx

def trace(env, callback):
        """Replace the ``step()`` method of *env* with a tracing function
        that calls *callbacks* with an events time, priority, ID and its
        instance just before it is processed.
   
        """
        def get_wrapper(env_step, callback):
            """Generate the wrapper for env.step()."""
            @wraps(env_step)
            def tracing_step():
                """Call *callback* for the next event if one exist before
                calling ``env.step()``."""
                if len(env._queue):
                    t, prio, eid, event = env._queue[0]
                    callback(t, prio, eid, event)
                return env_step()
            return tracing_step
        env.step = get_wrapper(env.step, callback)


def monitor(data, t, prio, eid, event):
    data.append((t, eid, type(event)))

def test_process(env):
    yield env.timeout(1)


if __name__ == "__main__":
    
    env = simpy.Environment()    
    myTP = TP(jsonFile='./test_graph.json', env=env)
    myTP.create_routing_table()
    # print(myTP.routingTable)

    # myTP.load_cyjs('./test_graph.json')

    testPacket1 = pk('test 1', 'a','e', 2048)
    testPacket2 = pk('test 2','b','c', 1)
    # # print("Packet delivery time for packet from a to b is: " + str(myTP.get_packet_delivery_time('b','a',testPacket)) + " Seconds")
    
    data = []

    monitor = partial(monitor, data)


    trace(env, monitor)

    # myTP.save_network_png('./test.png')

    env.process(myTP.queue_packet_for_transmition('a',testPacket1, 0))
    env.process(myTP.queue_packet_for_transmition('b',testPacket2, 0))
    env.process(myTP.process_recieved_packet(0.0001))
    env.process(myTP.transimition_loop(0.0001))
    env.run(until=5)
    # print(myTP.next_hop('a','d'))

    # for d in data:
    #     print(d)
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
