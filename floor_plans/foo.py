import numpy
import pyximport
pyximport.install(setup_args={"include_dirs":numpy.get_include()},
                  reload_support=True)

from time import time
import networkx as nx

from dijkstra import dijkstra
from dijkstrax import graph_shortest_path as dijkstrax

G = nx.grid_2d_graph(15, 15)

for i, j, data in G.edges(data=True):
    data['weight'] = 1

start = time()
foo = {vi: dijkstra(G, [vi], 'weight') for vi in G.nodes()}
print time() - start


start = time()
matrix = nx.to_scipy_sparse_matrix(G, weight=weight)
foo = {vi: dijkstrax(matrix) for vi in G.nodes()}
print time() - start
