
services = [['front1',{
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

nodes = {}
remainingRam = 4000
remainingCpu =4
for i in range(100):
    nodes[i] = [remainingRam, remainingCpu]

for i range(100):
    services