from collections import deque
from heapq import heappush, heappop
from itertools import count
import networkx as nx
from networkx.utils import generate_unique_node
import warnings as _warnings

def dijkstra(G, sources, weight, terminals):
    if type(terminals) is not set:
        terminals = set(terminals)

    paths = {source: [source] for source in sources}

    dist = {}  # dictionary of final distances
    seen = {}
    # fringe is heapq with 3-tuples (distance,c,node)
    # use the count c to avoid comparing nodes (may not be able to)
    c = count()
    fringe = []

    for source in sources:
        seen[source] = 0
        heappush(fringe, (0, next(c), source))

    while fringe:
        (d, _, v) = heappop(fringe)
        if v in dist:
            continue  # already searched this node.
        dist[v] = d
        for u, e in G.adj[v].items():
            # if (e['directed'] != None) and e['directed'] != u:
            #     continue
            cost = e[weight]
            vu_dist = dist[v] + cost
            if u in dist:
                if vu_dist < dist[u]:
                    raise ValueError('Contradictory paths found:',
                                     'negative weights?')
            elif u not in seen or vu_dist < seen[u]:
                seen[u] = vu_dist
                if u not in terminals:
                    heappush(fringe, (vu_dist, next(c), u))
                paths[u] = paths[v] + [u]

    return dist, paths
