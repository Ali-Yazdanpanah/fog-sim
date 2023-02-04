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
import random
import pyjion


START = 1
FINISH = 6
CHECK_INTERVAL = 0.05
SEND_RATE =100
REQUEST_COUNT = 300
NUM_APPS = 5
NUM_SERVICES = 5
CPU_PER_REQUEST = 0.5 
RAM_PER_REQUEST = 500 
NUM_RUNS = 10
INSTRUCTIONS_PER_REQUEST = 100
SIZE_OF_REQUEST = 32
APPS = AutoVivification()
placement_table = AutoVivification()
NUM_NODES = 50
GRAPH_FILE = './graphs/50node.json'


def send_requests(env, myTP, requests):
    zones = ['34','37','47','45']
    for i in range(REQUEST_COUNT):
        for j in range(4):
            zone = zones[random.randrange(len(zones))]
            testRequest = rq(name='TEST_APP_0 '+str(i) + "_" + str(j), source=zone, destinationService='APP_0_SERVICE_0' ,size=SIZE_OF_REQUEST, instructions=INSTRUCTIONS_PER_REQUEST, cpu=CPU_PER_REQUEST, ram=RAM_PER_REQUEST, sub=False, issuedBy=zone, masterService = 'none', masterRequest='none', env=env)
            # testRequest = rq(name='test '+str(i), source='zone_b', destinationService='front' ,size=SIZE_OF_REQUEST, instructions=10000000, cpu=0.5, ram=20, sub=False, issuedBy='zone_b', masterService = 'none', masterRequest='none', env=env)
            requests += [testRequest]
            env.process(myTP.queue_request_for_transmition(zone,testRequest, START + i/SEND_RATE))
            zone = zones[random.randrange(len(zones))]
            testRequest = rq(name='TEST_APP_1 '+str(i) + "_" + str(j), source=zone, destinationService='APP_1_SERVICE_0' ,size=SIZE_OF_REQUEST, instructions=INSTRUCTIONS_PER_REQUEST, cpu=CPU_PER_REQUEST, ram=RAM_PER_REQUEST, sub=False, issuedBy=zone, masterService = 'none', masterRequest='none', env=env)
            # testRequest = rq(name='test '+str(i), source='zone_b', destinationService='front' ,size=SIZE_OF_REQUEST, instructions=10000000, cpu=0.5, ram=20, sub=False, issuedBy='zone_b', masterService = 'none', masterRequest='none', env=env)
            requests += [testRequest]
            env.process(myTP.queue_request_for_transmition(zone,testRequest, START + i/SEND_RATE))
            zone = zones[random.randrange(len(zones))]
            testRequest = rq(name='TEST_APP_2 '+str(i) + "_" + str(j), source=zone, destinationService='APP_2_SERVICE_0' ,size=SIZE_OF_REQUEST, instructions=INSTRUCTIONS_PER_REQUEST, cpu=CPU_PER_REQUEST, ram=RAM_PER_REQUEST, sub=False, issuedBy=zone, masterService = 'none', masterRequest='none', env=env)
            # testRequest = rq(name='test '+str(i), source='zone_b', destinationService='front' ,size=SIZE_OF_REQUEST, instructions=10000000, cpu=0.5, ram=20, sub=False, issuedBy='zone_b', masterService = 'none', masterRequest='none', env=env)
            requests += [testRequest]
            env.process(myTP.queue_request_for_transmition(zone,testRequest, START + i/SEND_RATE))
            zone = zones[random.randrange(len(zones))]
            testRequest = rq(name='TEST_APP_3 '+str(i) + "_" + str(j), source=zone, destinationService='APP_3_SERVICE_0' ,size=SIZE_OF_REQUEST, instructions=INSTRUCTIONS_PER_REQUEST, cpu=CPU_PER_REQUEST, ram=RAM_PER_REQUEST, sub=False, issuedBy=zone, masterService = 'none', masterRequest='none', env=env)
            # testRequest = rq(name='test '+str(i), source='zone_b', destinationService='front' ,size=SIZE_OF_REQUEST, instructions=10000000, cpu=0.5, ram=20, sub=False, issuedBy='zone_b', masterService = 'none', masterRequest='none', env=env)
            requests += [testRequest]
            env.process(myTP.queue_request_for_transmition(zone,testRequest, START + i/SEND_RATE))
            zone = zones[random.randrange(len(zones))]
            testRequest = rq(name='TEST_APP_4 '+str(i) + "_" + str(j), source=zone, destinationService='APP_4_SERVICE_0' ,size=SIZE_OF_REQUEST, instructions=INSTRUCTIONS_PER_REQUEST, cpu=CPU_PER_REQUEST, ram=RAM_PER_REQUEST, sub=False, issuedBy=zone, masterService = 'none', masterRequest='none', env=env)
            # testRequest = rq(name='test '+str(i), source='zone_b', destinationService='front' ,size=SIZE_OF_REQUEST, instructions=10000000, cpu=0.5, ram=20, sub=False, issuedBy='zone_b', masterService = 'none', masterRequest='none', env=env)
            requests += [testRequest]
            env.process(myTP.queue_request_for_transmition(zone,testRequest, START + i/SEND_RATE))



def start(): 

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
    myTP = TP(jsonFile=GRAPH_FILE, env=env)
    myTP.create_routing_table()
    # print(myTP.routingTable)

    myTP.load_cyjs(GRAPH_FILE)


    for i in range(NUM_APPS):
        APPS['APP_'+str(i)] = []    
    

    for i in range(NUM_APPS):
        for j in range(NUM_SERVICES):
            APPS['APP_'+str(i)] += [['APP_'+str(i)+'_SERVICE_'+str(j),AutoVivification()]]
            if j != NUM_SERVICES-1:
                APPS['APP_'+str(i)][j][1]['needs'] = ['APP_'+str(i)+'_SERVICE_'+str(j+1)]

    # service_placement = []

    # for i in range(NUM_NODES):
    #     service_placement += [[]]

    # # print(service_placement)
    total_instances = 0
    for app in APPS:
        for j in range(NUM_SERVICES):
            APPS[app][j][1]['instances'] = random.randrange(5,6)
            total_instances += APPS[app][j][1]['instances']
    # print(random.randrange(50))

    ram_per_instance = 8000*50/total_instances
    cpu_per_instance = 8*50/total_instances
    instance_per_device_ram = 8000/ram_per_instance
    instance_per_device_cpu = 8/cpu_per_instance
    instance_per_service = int(min(instance_per_device_cpu, instance_per_device_ram))
    # print("MAX RAM PER DEVICE: ", ram_per_instance)
    # print("MAX CPU PER DEVICE: ", cpu_per_instance)
    # print("MAX INSTANCE PER DEVICE: ", instance_per_service)


    # for i in range(NUM_APPS):
    #     for j in range(NUM_SERVICES):
    #         APPS['APP_'+str(i)][j][1]['RAM'] = round(ram_per_instance,2)
    #         APPS['APP_'+str(i)][j][1]['CPU'] = round(cpu_per_instance,2)

    # for app in APPS:
    #     for service in APPS[app]:
    #         placement_table[service[0]] = service[1] 

    # for service in placement_table:
    #     for node in range(len(service_placement)):
    #         placement_table[service]['deployments'][node]['replicas'] = 0

    # for service in placement_table:
    #     for i in range(placement_table[service]['instances']):
    #         candidate_node_number = random.randrange(len(service_placement))
    #         candidate_node = service_placement[candidate_node_number]
    #         while len(candidate_node) >= instance_per_service:
    #             candidate_node_number = random.randrange(len(service_placement))
    #             candidate_node = service_placement[candidate_node_number]
    #         candidate_node += [service]
    #         placement_table[service]['deployments'][candidate_node_number]['replicas'] += 1



    # for i in range(len(service_placement)):
    #     print("================================================================\n")
    #     print("node: " + str(i))
    #     print("-------------")
    #     for service in service_placement[i]:
    #         print(service)
    #     print('\n')

    # for service in placement_table:
    #     print("================================================================\n")
    #     print(service)
    #     print("-------------")
    #     print(placement_table[service])
    #     print('\n')




 
    # new = services

    compute_nodes = [node[0] for node in myTP.get_compute_nodes()]
    # 6 nods, 3 services
    # input_array = np.array(service_mapping_matrix)
    # for index in range(len(input_array)):
    #     for index2 in range(len(compute_nodes)):
    #         services[index][1]['deployments'][compute_nodes[index2]]['replicas'] = input_array[index][index2]
    # print(services == new)
 # # print("Packet delivery time for request from a to b is: " + str(myTP.get_request_delivery_time('b','a',testPacket)) + " Seconds")

    
    data = []

    # monitor = partial(monitor, data)


    # trace(env, monitor)

    # myTP.save_network_png('./test.png')
    # env.process(myTP.create_service_table(services))
    # env.process(myTP.create_service_placement_table(services))
    # env.process(myTP.place_services())
    # env.process(myTP.get_all_service_nodes('front'))
    # print("1")
    requests = []

    send_requests(env,myTP,requests)

            # testRequest = rq(name='TEST_APP_5 '+str(i), source='47', destinationService='APP_5_SERVICE_0' ,size=SIZE_OF_REQUEST, instructions=10000, cpu=0.1, ram=100, sub=False, issuedBy='47', masterService = 'none', masterRequest='none', env=env)
            # # testRequest = rq(name='test '+str(i), source='zone_b', destinationService='front' ,size=SIZE_OF_REQUEST, instructions=10000000, cpu=0.5, ram=20, sub=False, issuedBy='zone_b', masterService = 'none', masterRequest='none', env=env)
            # requests += [testRequest]
            # env.process(myTP.queue_request_for_transmition('47',testRequest, START + i/SEND_RATE))
    
            # testRequest = rq(name='TEST_APP_6 '+str(i), source='45', destinationService='APP_6_SERVICE_0' ,size=SIZE_OF_REQUEST, instructions=10000, cpu=0.1, ram=100, sub=False, issuedBy='45', masterService = 'none', masterRequest='none', env=env)
            # # testRequest = rq(name='test '+str(i), source='zone_b', destinationService='front' ,size=SIZE_OF_REQUEST, instructions=10000000, cpu=0.5, ram=20, sub=False, issuedBy='zone_b', masterService = 'none', masterRequest='none', env=env)
            # requests += [testRequest]
            # env.process(myTP.queue_request_for_transmition('45',testRequest, START + i/SEND_RATE))

            # testRequest = rq(name='TEST_APP_8 '+str(i), source='37', destinationService='APP_8_SERVICE_0' ,size=SIZE_OF_REQUEST, instructions=10000, cpu=0.1, ram=100, sub=False, issuedBy='45', masterService = 'none', masterRequest='none', env=env)
            # # testRequest = rq(name='test '+str(i), source='zone_b', destinationService='front' ,size=SIZE_OF_REQUEST, instructions=10000000, cpu=0.5, ram=20, sub=False, issuedBy='zone_b', masterService = 'none', masterRequest='none', env=env)
            # requests += [testRequest]
            # env.process(myTP.queue_request_for_transmition('37',testRequest, START + i/SEND_RATE))

            # testRequest = rq(name='TEST_APP_9 '+str(i), source='34', destinationService='APP_9_SERVICE_0' ,size=SIZE_OF_REQUEST, instructions=10000, cpu=0.1, ram=100, sub=False, issuedBy='34', masterService = 'none', masterRequest='none', env=env)
            # # testRequest = rq(name='test '+str(i), source='zone_b', destinationService='front' ,size=SIZE_OF_REQUEST, instructions=10000000, cpu=0.5, ram=20, sub=False, issuedBy='zone_b', masterService = 'none', masterRequest='none', env=env)
            # requests += [testRequest]
            # env.process(myTP.queue_request_for_transmition('34',testRequest, START + i/SEND_RATE))



    # # print("2")
    uptime = 0
    for i in range(START,FINISH):
            uptime += 1
            for q in range(int(1/CHECK_INTERVAL)):
                # print("record time: ", i+(q*CHECK_INTERVAL))
                start_delayed(myTP.env,myTP.get_utilization_rates(), i+(q*CHECK_INTERVAL))

    cost = AutoVivification()

    # print("3")
    # env.process(myTP.queue_request_for_transmition('zone_a',testRequest3, 2))
    # env.process(myTP.choose_request_destination('a',testRequest3))
    # env.process(myTP.create_service_placement_table(services))
    # env.process(myTP.process_recieved_requests_loop())
    env.process(myTP.start())
    env.process(myTP.create_service_placement_table(NUM_APPS=NUM_APPS, NUM_SERVICES=NUM_SERVICES))
    env.process(myTP.place_services())
    env.run(until=FINISH)
    # print(myTP.next_hop('a','d'))
    stats = Statistics()
    results = AutoVivification()
    myTP.set_endtime(requests)
    myTP.stats.calculate_average_response_time(requests)
    
    # # myTP.stats.print_average_intra_latency()
    # print('CPU: ',myTP.all_cpu_utilization_average())
    # print('MEM: ',myTP.all_mem_utilization_average())
    # print('COST: ',cost)
    results['AVG_LATENCY'] = stats.calculate_average_response_time(requests)
    results['AVG_INTRA_LATENCY'] = myTP.stats.get_average_intra_latency()
    results['CPU'] = myTP.all_cpu_utilization_average()
    results['MEM'] = myTP.all_mem_utilization_average()
    results['CLOUD_REQS'] = myTP.get_cloud_reqs()
    memAvg = myTP.all_mem_utilization()
    x_axis = []
    y_axis = []

    for key in memAvg:
        x_axis.append(key)
        y_axis.append(memAvg[key])
    plt.plot(x_axis, y_axis)
    plt.title('mem Average')
    plt.xlabel('time')
    plt.ylabel('utilization rate')
    print('Count: ', myTP.REQUEST_COUNT)
    plt.show()
    # sum = 0 
    # for i in cost.values():
    #     sum += i
    # avg_cost = sum / len(node[1])
    # print('AVG_COST : '  , avg_cost)

    results['COST'] = myTP.all_costs() 
    results['TIME'] = myTP.stats.endtime - myTP.stats.starttime
    results['START_TIME'] = myTP.stats.starttime
    results['END_TIME'] = myTP.stats.endtime
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
    pyjion.enable()
    pyjion.config(pgc=True)
    pyjion.config(level=0)
    all_results = []
    # with open('./test_graph.json', 'r') as file:
        # networkData = file.read()
        # networkDataJson = js.loads(networkData)
    for i in range(NUM_RUNS):
        all_results.append(start())
        print("Run ", str(i) + ": ", all_results[-1])

