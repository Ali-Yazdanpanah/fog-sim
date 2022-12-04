from network import Topology as TP
from network import Request as rq
from functools import partial, wraps
from stats import Statistics
# from Topology import return_weight
from simpy.util import start_delayed
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

    myTP.load_cyjs('./test_graph.json')



    services = [
    ('front',{
        'deployments':{
            'a':{ 'replicas' : 0 },
            'b':{ 'replicas' : 0 },
            'd':{ 'replicas' : 0 },
            'e':{ 'replicas' : 0 },
            'f':{ 'replicas' : 0 },
            'CLOUD': { 'replicas' : 100}
        },
        'RAM': 5000,
        'CPU': 10,
        'needs': ['back','back2'],

    }),
    ('back',{
        'deployments':{
            'a':{ 'replicas' : 1 },
            'b':{ 'replicas' : 1 },
            'd':{ 'replicas' : 2 },
            'e':{ 'replicas' : 3 },
            'f':{ 'replicas' : 1 },
            'CLOUD': { 'replicas' : 100}
        },
        'RAM': 5000,
        'CPU': 10,
        'needs': []
    }),
    ('back2',{
        'deployments':{
            'a':{ 'replicas' : 2 },
            'b':{ 'replicas' : 2 },
            'd':{ 'replicas' : 1 },
            'e':{ 'replicas' : 2 },
            'f':{ 'replicas' : 0 },
            'CLOUD': { 'replicas' : 0}
        },
        'RAM': 8000,
        'CPU': 10,
        'needs': []
    })
    ]

 # # print("Packet delivery time for request from a to b is: " + str(myTP.get_request_delivery_time('b','a',testPacket)) + " Seconds")

    
    data = []

    monitor = partial(monitor, data)


    trace(env, monitor)

    # myTP.save_network_png('./test.png')
    env.process(myTP.create_service_table(services))
    env.process(myTP.create_service_placement_table(services))
    env.process(myTP.place_services())
    # env.process(myTP.get_all_service_nodes('front'))
    # print("1")
    requests = []
    for i in range(21):
            testRequest = rq(name='test '+str(i), source='zone_a', destinationService='front' ,size=24, instructions=1000000, cpu=1, ram=20, sub=False, issuedBy='zone_a', masterService = 'none', masterRequest='none', env=env)
            requests += [testRequest]
            env.process(myTP.queue_request_for_transmition('zone_a',testRequest, 10 + i/50))
    # print("2")
    for i in range(9,14):
            start_delayed(myTP.env, myTP.get_utilization_rates(), i)
            start_delayed(myTP.env,myTP.get_utilization_rates(), i+0.5)

    # print("3")
    # env.process(myTP.queue_request_for_transmition('zone_a',testRequest3, 2))
    # env.process(myTP.choose_request_destination('a',testRequest3))
    # env.process(myTP.create_service_placement_table(services))
    # env.process(myTP.process_recieved_requests_loop())
    env.process(myTP.start())

    env.run(until=200)
    # print(myTP.next_hop('a','d'))
    stats = Statistics()
    stats.calculate_average_response_time(requests)
    myTP.stats.print_average_intra_latency()
    print('CPU util avg: ',myTP.all_cpu_utilization_average())
    print('MEM util avg: ',myTP.all_mem_utilization_average())
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
