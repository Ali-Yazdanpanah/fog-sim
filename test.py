import networkx as nx
import json as js
import matplotlib.pyplot as plt

options = {
    'node_color': 'black',
    'node_size': 100,
    'width': 3,
}
G = nx.Graph()

G.add_edge("a", "b", weight=0.5)
G.add_edge("a", "c", weight=0.5)
G.add_edge("c", "d", weight=0.5)
G.add_edge("c", "e", weight=0.5)
G.add_edge("c", "f", weight=0.5)
G.add_edge("a", "d", weight=0.5)

elarge = [(u, v) for (u, v, d) in G.edges(data=True) if d["weight"] > 0.5]
esmall = [(u, v) for (u, v, d) in G.edges(data=True) if d["weight"] <= 0.5]

pos = nx.spring_layout(G, seed=7)  # positions for all nodes - seed for reproducibility

# nodes
nx.draw_networkx_nodes(G, pos, node_size=700)

# edges
nx.draw_networkx_edges(G, pos, edgelist=elarge, width=6)
nx.draw_networkx_edges(
    G, pos, edgelist=esmall, width=6, alpha=0.5, edge_color="b", style="dashed"
)

# node labels
nx.draw_networkx_labels(G, pos, font_size=20, font_family="sans-serif")
# edge weight labels
edge_labels = nx.get_edge_attributes(G, "weight")
nx.draw_networkx_edge_labels(G, pos, edge_labels)

ax = plt.gca()
ax.margins(0.08)
plt.axis("off")
plt.tight_layout()
plt.show()


# To save drawings to a file, use, for example

nx.draw(G)
cyjsGraph = nx.cytoscape_data(G)
graphAddress = './test_graph.json'
with open(graphAddress, 'w') as file:
    js.dump(cyjsGraph,file, indent=4)
# plt.savefig("path.png")