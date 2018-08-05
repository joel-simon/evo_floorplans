from collection import defaultdict

class Graph(object):
    """docstring for Graph"""
    def __init__(self, genome):
        self.arg = arg
        nodes = list(genome.node_genes.keys())
        edges = defaultdict(list)

        for conn in genome.conn_genes:
            edges[conn.in_node_id].append(conn.out_node_id)
            edges[conn.out_node_id].append(conn.in_node_id)

def shortest_path(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return path
    if start not in graph.nodes:
        return None
    shortest = None
    for node in graph[start]:
        if node not in path:
            newpath = find_shortest_path(graph, node, end, path)
            if newpath:
                if not shortest or len(newpath) < len(shortest):
                    shortest = newpath
    return shortest
