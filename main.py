from network import Topology as TP
from network import Request as rq
from functools import partial, wraps
from stats import Statistics
# from Topology import return_weight
from simpy.util import start_delayed
import simpy
import matplotlib.pyplot as plt
import networkx as nx
from util import AutoVivification
import numpy as np






def test_process(env):
    yield env.timeout(1)

def start(service_mapping_matrix): 

    def monitor(data, t, prio, eid, event):
        data.append((t, eid, type(event))) 

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
        
    env = simpy.Environment()    
    myTP = TP(jsonFile='./test_graph.json', env=env)
    myTP.create_routing_table()
    # print(myTP.routingTable)

    myTP.load_cyjs('./test_graph.json')

    START = 9
    FINISH = 12
    CHECK_INTERVAL = 0.1
    SEND_RATE = 10
    REQUEST_COUNT = 100





    services = [['front',{
        'deployments':{
            'a':{ 'replicas' : 1 },
            'b':{ 'replicas' : 0 },
            'd':{ 'replicas' : 0 },
            'e':{ 'replicas' : 5 },
            'f':{ 'replicas' : 0 },
            'g':{ 'replicas' : 0 },
            'h':{ 'replicas' : 0 },
            'j':{ 'replicas' : 5 },
            'k':{ 'replicas' : 0 },
            'l':{ 'replicas' : 0 },
            'm':{ 'replicas' : 0 },
            'n':{ 'replicas' : 5 },
            'o':{ 'replicas' : 0 },
            'p':{ 'replicas' : 0 },
            'CLOUD': { 'replicas' : 100}
        },
        'RAM': 5000,
        'CPU': 10,
        'needs': ['back','back2'],

    }],
    ['back',{
        'deployments':{
            'a':{ 'replicas' : 1 },
            'b':{ 'replicas' : 1 },
            'd':{ 'replicas' : 2 },
            'e':{ 'replicas' : 3 },
            'f':{ 'replicas' : 1 },
            'g':{ 'replicas' : 0 },
            'h':{ 'replicas' : 0 },
            'j':{ 'replicas' : 5 },
            'k':{ 'replicas' : 0 },
            'l':{ 'replicas' : 0 },
            'm':{ 'replicas' : 0 },
            'n':{ 'replicas' : 5 },
            'o':{ 'replicas' : 0 },
            'p':{ 'replicas' : 0 },
            'CLOUD': { 'replicas' : 100}
        },
        'RAM': 5000,
        'CPU': 10,
        'needs': []
    }],
    ['back2',{
        'deployments':{
            'a':{ 'replicas' : 2 },
            'b':{ 'replicas' : 2 },
            'd':{ 'replicas' : 1 },
            'e':{ 'replicas' : 2 },
            'f':{ 'replicas' : 0 },
            'g':{ 'replicas' : 0 },
            'h':{ 'replicas' : 1 },
            'j':{ 'replicas' : 5 },
            'k':{ 'replicas' : 0 },
            'l':{ 'replicas' : 1 },
            'm':{ 'replicas' : 1 },
            'n':{ 'replicas' : 5 },
            'o':{ 'replicas' : 0 },
            'p':{ 'replicas' : 0 },
            'CLOUD': { 'replicas' : 100}
        },
        'RAM': 8000,
        'CPU': 10,
        'needs': []
    }]]

    # new = services

    compute_nodes = [node[0] for node in myTP.get_compute_nodes()]
    # 6 nods, 3 services
    input_array = np.array(service_mapping_matrix)
    for index in range(len(input_array)):
        for index2 in range(len(compute_nodes)):
            services[index][1]['deployments'][compute_nodes[index2]]['replicas'] = input_array[index][index2]
    # print(services == new)
 # # print("Packet delivery time for request from a to b is: " + str(myTP.get_request_delivery_time('b','a',testPacket)) + " Seconds")

    
    data = []

    monitor = partial(monitor, data)


    trace(env, monitor)

    myTP.save_network_png('./test.png')
    env.process(myTP.create_service_table(services))
    env.process(myTP.create_service_placement_table(services))
    env.process(myTP.place_services())
    # env.process(myTP.get_all_service_nodes('front'))
    # print("1")
    requests = []

    for i in range(REQUEST_COUNT):
            testRequest = rq(name='test '+str(i), source='zone_a', destinationService='front' ,size=24, instructions=1000000, cpu=0.2, ram=20, sub=False, issuedBy='zone_a', masterService = 'none', masterRequest='none', env=env)
            # testRequest = rq(name='test '+str(i), source='zone_b', destinationService='front' ,size=24, instructions=1000000, cpu=0.5, ram=20, sub=False, issuedBy='zone_b', masterService = 'none', masterRequest='none', env=env)
            requests += [testRequest]
            env.process(myTP.queue_request_for_transmition('zone_a',testRequest, START + i/SEND_RATE))
    # print("2")
    uptime = 0
    for i in range(START,FINISH+1):
            uptime += 1
            for q in range(int(1/CHECK_INTERVAL)):
                start_delayed(myTP.env,myTP.get_utilization_rates(), i+(q*CHECK_INTERVAL))

    cost = AutoVivification()
    for node in myTP.G.nodes(data=True):
        try:
            cost[node[0]] = node[1]['COST'] * uptime
        except:
            pass

    
    # print("3")
    # env.process(myTP.queue_request_for_transmition('zone_a',testRequest3, 2))
    # env.process(myTP.choose_request_destination('a',testRequest3))
    # env.process(myTP.create_service_placement_table(services))
    # env.process(myTP.process_recieved_requests_loop())
    env.process(myTP.start())

    env.run(until=200)
    # print(myTP.next_hop('a','d'))
    stats = Statistics()
    results = AutoVivification()
    # stats.calculate_average_response_time(requests)
    # myTP.stats.print_average_intra_latency()
    # print('CPU: ',myTP.all_cpu_utilization_average())
    # print('MEM: ',myTP.all_mem_utilization_average())
    # print('COST: ',cost)
    results['AVG_LATENCY'] = stats.calculate_average_response_time(requests)
    results['AVG_INTRA_LATENCY'] = myTP.stats.get_average_intra_latency()
    results['CPU'] = myTP.all_cpu_utilization_average()
    results['MEM'] = myTP.all_mem_utilization_average()

    sum = 0 
    for i in cost.values():
        sum += i
    avg_cost = sum / len(node[1])
    print('AVG_COST : '  , avg_cost)

    results['COST'] = cost 
    return results 
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


if __name__ == "__main__":
    results = start([[1, 2, 1, 1, 1, 1, 0, 1, 0, 1, 2, 3, 0 , 1,100], [1 ,1 ,1, 2, 1, 2, 1, 2, 3, 1, 2, 1, 1, 1, 100], [0 , 0, 1, 1, 1 ,2, 2, 1, 2, 0, 1, 2, 3, 3, 100]])
    print(results)
