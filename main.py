from network import Topology as TP
from network import Request as rq
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



    services = [
    ('front',{
        'deployments':{
            'a':{ 'replicas' : 1 },
            'b':{ 'replicas' : 1 },
            'd':{ 'replicas' : 1 },
            'e':{ 'replicas' : 1 },
            'f':{ 'replicas' : 1 }
        },
        'RAM': 1024,
        'CPU': 2,
        'needs': 'back',

    }),
    ('back',{
        'deployments':{
            'a':{ 'replicas' : 0 },
            'b':{ 'replicas' : 0 },
            'd':{ 'replicas' : 0 },
            'e':{ 'replicas' : 2 },
            'f':{ 'replicas' : 2 }
        },
        'RAM': 2048,
        'CPU': 4
    })
    ]

    testRequest1 = rq('test 1', 'a', 'front', 'e' , 2048, 1000000, 5, 10240)
    testRequest2 = rq('test 2', 'b', 'front', 'f' ,2048, 1000000, 5, 10240)
    testRequest3 = rq('test 3', 'b', 'front', 'f' ,2048, 1000000, 5, 10240)
    # # print("Packet delivery time for request from a to b is: " + str(myTP.get_request_delivery_time('b','a',testPacket)) + " Seconds")
    
    data = []

    monitor = partial(monitor, data)


    trace(env, monitor)

    # myTP.save_network_png('./test.png')
    env.process(myTP.create_service_placement_table(services))
    # env.process(myTP.get_all_service_nodes('front'))
    env.process(myTP.queue_request_for_transmition('a',testRequest1, 2))
    env.process(myTP.queue_request_for_transmition('b',testRequest2, 2))
    env.process(myTP.queue_request_for_transmition('b',testRequest3, 2))
    # env.process(myTP.process_recieved_requests_loop())
    env.process(myTP.start())
    
    env.run(until=100)
    # print(myTP.next_hop('a','d'))

    # for d in data:
    #     print(d)
    # print("Propgation time of d to c is: " + str(myTP.get_request_delivery_time('d','c')))
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
