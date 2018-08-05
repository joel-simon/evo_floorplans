import math
from collections import defaultdict
from itertools import combinations
from random import choice, gauss, randint, random, shuffle, sample

from floor_plans.genes import NodeGene, ConnectionGene, AttributeGene
from floor_plans.random_util import weighted_choice

class Genome(object):
    """ A genome for general recurrent neural networks. """
    def __init__(self, ID, config, parent1_id, parent2_id, variable_room_types):
        self.ID = ID
        self.config = config

        # (id, gene) pairs for connection and node gene sets.
        self.conn_genes = {}
        self.node_genes = {}
        self.mutateable_nodes = []

        self.attribute_genes = {}
            # 'hallway_alpha': [12, [10, 14]]
        # }
        # self.hallway_alpha = 12.0
        # self.hallway_alpha_bounds = [10., 14]
        # self.hallway_k = 10.

        self.fitnesses = {}
        self.fitness = None
        self.species_id = None

        # my parents id: helps in tracking genome's genealogy
        self.parent1_id = parent1_id
        self.parent2_id = parent2_id

        self.phenotype = None # save to avoid repeat evalaution.
        self.variable_room_types = variable_room_types

    def mutate(self, innovation_indexer):
        """ Mutates this genome """
        # heat = choice([1, 2, 3])
        events = [
            (.1, self.mutate_add_node),
            (.05, self.mutate_delete_node),
            # (.1, self.mutate_add_node_between),

            (.1, self.mutate_attributes),

            (.2, self.mutate_add_connection),
            (.1, self.mutate_delete_connection),
            # (.1, self.mutate_nodes),
            (.1, self.mutate_connections),
            (.1, self.mutate_move_connnection),

            # (.5, self.mutate_switch_rooms),
            (.2, self.mutate_shuffle_rooms),
        ]
        # for i in range(heat):
        #     weighted_choice(events)(innovation_indexer)
        for p, e in events:
            if random() < p:
                e(innovation_indexer)
        return self

    def mutate_nodes(self, innovation_indexer):
        # options = [ n.ID for n in self.node_genes.values() if not n.required ]
        options = self.mutateable_nodes
        if len(options):
            choice(options).mutate(self.config)

    def mutate_move_connnection(self, innovation_indexer):
        conn = choice(list(self.conn_genes.values()))
        if not conn.fixed:
            new_node_id = choice(list(self.node_genes.keys()))
            if new_node_id != conn.in_node_id and new_node_id != conn.out_node_id:
                if random() > .5:
                    conn.in_node_id = new_node_id
                else:
                    conn.out_node_id = new_node_id

    def mutate_switch_rooms(self, innovation_indexer):
        raise NotImplementedError()

    def mutate_attributes(self, innovation_indexer):
        choice(list(self.attribute_genes.values())).mutate()

    def mutate_connections(self, innovation_indexer):
        choice(list(self.conn_genes.values())).mutate(self.config)

    def mutate_shuffle_rooms(self, innovation_indexer=None):
        """ Swap the connections between pairs of nodes. """

        rooms = list(self.node_genes.keys())
        shuffle(rooms)
        # n = choice([1, len(rooms)//2]) # n = how many pairs.
        n = 1
        mapping = dict()

        for i in range(0, n*2, 2):
            mapping[rooms[i]] = rooms[i+1]
            mapping[rooms[i+1]] = rooms[i]

        # print('mapping=', mapping)
        for conn in self.conn_genes.values():
            if not conn.fixed:
                if conn.in_node_id in mapping:
                    conn.in_node_id = mapping[conn.in_node_id]

                if conn.out_node_id in mapping:
                    conn.out_node_id = mapping[conn.out_node_id]

    def crossover(self, other, child_id):
        """ Crosses over parents' genomes and returns a child. """

        # Parents must belong to the same species.
        assert self.species_id == other.species_id, 'Different parents species ID: {0} vs {1}'.format(self.species_id,
                                                                                                      other.species_id)

        # TODO: if they're of equal fitness, choose the shortest
        if self.fitness > other.fitness:
            parent1 = self
            parent2 = other
        else:
            parent1 = other
            parent2 = self

        # creates a new child
        child = self.__class__(child_id, self.config, self.ID, other.ID, self.variable_room_types)

        child.inherit_genes(parent1, parent2)

        child.species_id = parent1.species_id

        return child

    def inherit_genes(self, parent1, parent2):
        """ Applies the crossover operator. """
        assert (parent1.fitness >= parent2.fitness)

        # Crossover connection genes
        for cg1 in parent1.conn_genes.values():
            try:
                cg2 = parent2.conn_genes[cg1.key]
            except KeyError:
                # Copy excess or disjoint genes from the fittest parent
                self.conn_genes[cg1.key] = cg1.copy()
            else:
                if cg2.is_same_innov(cg1):  # Always true for *global* INs
                    # Homologous gene found
                    new_gene = cg1.get_child(cg2)
                else:
                    new_gene = cg1.copy()
                self.conn_genes[new_gene.key] = new_gene

        # Crossover node genes
        for ng1_id, ng1 in parent1.node_genes.items():
            ng2 = parent2.node_genes.get(ng1_id)
            if ng2 is None:
                # copies extra genes from the fittest parent
                new_gene = ng1.copy()
            else:
                # matching node genes
                new_gene = ng1.get_child(ng2)

            assert new_gene.ID not in self.node_genes
            self.node_genes[new_gene.ID] = new_gene

        # Crossover attribute genes.
        assert(len(parent1.attribute_genes) == len(parent2.attribute_genes))
        for name, ag1 in parent1.attribute_genes.items():
            ag2 = parent2.attribute_genes[name]
            self.attribute_genes[name] = ag1.get_child(ag2)

        assert len(self.conn_genes)

    def get_new_node_id(self):
        new_id = 0
        while new_id in self.node_genes:
            new_id += 1
        return new_id

    # def mutate_add_node_between(self, innovation_indexer):
    #     conn_to_split = choice(list(self.conn_genes.values()))
    #     new_node_id = self.get_new_node_id()
    #     size = 10 + random() * 5
    #     ng = NodeGene(new_node_id, size, name='empty')
    #     assert ng.ID not in self.node_genes
    #     self.node_genes[ng.ID] = ng
    #     new_conn1, new_conn2 = conn_to_split.split(innovation_indexer, ng.ID)
    #     self.conn_genes[new_conn1.key] = new_conn1
    #     self.conn_genes[new_conn2.key] = new_conn2
    #     return ng, conn_to_split  # the return is only used in genome_feedforward

    def mutate_add_node(self, innovation_indexer):
        if len(self.variable_room_types) == 0:
            return

        num_connections = 2
        connect_to = sample(list(self.node_genes.values()), num_connections)
        new_room_type, new_room_size = choice(self.variable_room_types)

        radius = math.sqrt(new_room_size/math.pi)
        new_node_id = self.get_new_node_id()
        ng = NodeGene(new_node_id, radius, name=new_room_type, required=False)

        self.node_genes[ng.ID] = ng
        for ng1 in connect_to:
            self.connect(ng.ID, ng1.ID, innovation_indexer)

        self.mutateable_nodes.append(ng.ID)

    def mutate_add_connection(self, innovation_indexer):
        in_node, out_node = sample(list(self.node_genes.values()), 2)
        # Only create the connection if it doesn't already exist.
        key = tuple(sorted((in_node.ID, out_node.ID)))
        if key not in self.conn_genes:
            self.connect(in_node.ID, out_node.ID, innovation_indexer, added=True)

    def mutate_delete_node(self, innovation_indexer):
        # options = [ n.ID for n in self.node_genes.values() if not n.required ]
        options = self.mutateable_nodes
        # Do nothing if there are no hidden nodes.
        if len(options) == 0:
            return -1

        node_id = choice(options)
        node = self.node_genes[node_id]

        keys_to_delete = set()
        for key, value in self.conn_genes.items():
            if value.in_node_id == node_id or value.out_node_id == node_id:
                keys_to_delete.add(key)

        # Do not allow deletion of all connection genes.
        if len(keys_to_delete) >= len(self.conn_genes):
            return -1

        for key in keys_to_delete:
            del self.conn_genes[key]

        del self.node_genes[node_id]
        self.mutateable_nodes.remove(node_id)
        return node_id

    def mutate_delete_connection(self, innovation_indexer):
        options = list(self.conn_genes.values())#list(self.conn_genes.keys())#[key for key, c in self.conn_genes.items() if c.added]
        if len(options):
            key = choice(options).key
            # try:
            del self.conn_genes[key]
            # except KeyError as e:
            #     # print(e)
            #     print(key, key in self.conn_genes)
            #     print(self.conn_genes.keys())

    # compatibility function
    def distance(self, other):
        """ Returns the distance between this genome and the other. """
        if len(self.conn_genes) > len(other.conn_genes):
            genome1 = self
            genome2 = other
        else:
            genome1 = other
            genome2 = self

        # Compute node gene differences.
        excess1 = sum(1 for k1 in genome1.node_genes if k1 not in genome2.node_genes)
        excess2 = sum(1 for k2 in genome2.node_genes if k2 not in genome1.node_genes)
        common_nodes = [k1 for k1 in genome1.node_genes if k1 in genome2.node_genes]

        size_diff = 0.0
        room_diff = 0

        for n in common_nodes:
            g1 = genome1.node_genes[n]
            g2 = genome2.node_genes[n]
            size_diff += math.fabs(g1.size - g2.size)

            if g1.name != g2.name:
                room_diff += 1

        most_nodes = max(len(genome1.node_genes), len(genome2.node_genes))
        distance = (self.config.excess_coefficient * float(excess1 + excess2) / most_nodes
                    + self.config.excess_coefficient * float(room_diff) / most_nodes
                    + self.config.weight_coefficient * (size_diff) / len(common_nodes))

        # Compute connection gene differences.
        if genome1.conn_genes:
            N = len(genome1.conn_genes)
            weight_diff = 0
            matching = 0
            disjoint = 0
            excess = 0

            max_cg_genome2 = None
            if genome2.conn_genes:
                max_cg_genome2 = max(genome2.conn_genes.values())

            for cg1 in genome1.conn_genes.values():
                try:
                    cg2 = genome2.conn_genes[cg1.key]
                except KeyError:
                    if max_cg_genome2 is not None and cg1 > max_cg_genome2:
                        excess += 1
                    else:
                        disjoint += 1
                else:
                    # Homologous genes
                    weight_diff += math.fabs(cg1.weight - cg2.weight)
                    matching += 1

            disjoint += len(genome2.conn_genes) - matching

            distance += self.config.excess_coefficient * float(excess) / N
            distance += self.config.disjoint_coefficient * float(disjoint) / N
            if matching > 0:
                distance += self.config.weight_coefficient * (weight_diff / matching)

        return distance

    def size(self):
        '''Returns genome 'complexity', taken to be (number of hidden nodes, number of enabled connections)'''
        num_hidden_nodes = len(self.node_genes)
        num_enabled_connections = len(self.conn_genes)
        return num_hidden_nodes, num_enabled_connections

    def __lt__(self, other):
        '''Order genomes by fitness.'''
        return self.fitness < other.fitness

    def __str__(self):
        s = "Nodes:"
        for ng in self.node_genes.values():
            s += "\n\t" + str(ng)
        s += "\nConnections:"
        connections = list(self.conn_genes.values())
        connections.sort()
        for c in connections:
            s += "\n\t" + str(c)
        return s

    def connect(self, id_a, id_b, innovation_indexer, weight=None, fixed=False, added=False):
        assert type(id_a) is int
        assert type(id_b) is int
        assert id_a != id_b
        if weight is None:
            weight = random()
        innovation_id = innovation_indexer.get_innovation_id(id_a, id_b)
        cg = ConnectionGene(innovation_id, id_a, id_b, weight, fixed, added)
        self.conn_genes[cg.key] = cg

    def compute_full_connections(self):
        connections = []
        for id1 in self.node_genes:
            for id2 in self.node_genes:
                if id1 < id2:
                    connections.append((id1, id2))
        return connections

    def connect_full(self, innovation_indexer):
        """ Create a fully-connected genome. """
        for input_id, output_id in self.compute_full_connections():
            self.connect(input_id, output_id, innovation_indexer)

    def connect_partial(self, innovation_indexer, count):
        assert type(count) is int
        assert count > 0
        ids = set(self.node_genes.keys())
        for id1 in self.node_genes:
            for id2 in sample(ids.difference([id1]), count):
                self.connect(id1, id2, innovation_indexer)
        # assert 0 <= fraction <= 1
        # all_connections = self.compute_full_connections()
        # shuffle(all_connections)
        # num_to_add = int(round(len(all_connections) * fraction))
        # for input_id, output_id in all_connections[:num_to_add]:
        #     self.connect(input_id, output_id, innovation_indexer)
            # weight = random()
            # innovation_id = innovation_indexer.get_innovation_id(input_id, output_id)
            # cg = ConnectionGene(innovation_id, input_id, output_id, weight, True)
            # self.conn_genes[cg.key] = cg

    @classmethod
    def create(cls, ID, config, innovation_indexer):
        '''
        '''
        c = cls(ID, config, None, None, config.spec.variable_room_types)
        node_id = 0

        name_groups = defaultdict(set)



        # Create node genes based off of rooms in spec.
        for _, room in config.spec.nodes(True):
            assert node_id not in c.node_genes
            name = room['name']
            name_groups[name].add(node_id)
            size = math.sqrt(room['area']/math.pi)
            c.node_genes[node_id] = NodeGene(node_id, size, name, required=True)
            node_id += 1

        # Create mandatory edges.
        connected = []
        for id1, id2, data in config.spec.edges(data=True):
            weight = 1.0 if data['type'] == 'adjacent' else random()*.5
            c.connect(id1, id2, innovation_indexer, weight, fixed=True)
            connected.append(id1)
            connected.append(id2)

        # for name, group in name_groups.items():
        #     if len(group) > 1 and name != 'toilet' and name != 'empty':
        #         for nid1 in group:
        #             nid2 = choice(list(set(group)-{nid1}))
        #             connected.append(nid1)
        #             connected.append(nid2)
        #             c.connect(nid1, nid2, innovation_indexer, weight=1.0)

        # foo = combinations(set(c.node_genes.keys()) - set(connected), 2)
        # edges = sample(list(foo), int(len(c.node_genes)))
        # for i, j in edges:
        #     c.connect(i, j, innovation_indexer, weight=.1)

        # Create random edges.
        genes = list(c.node_genes.keys())
        shuffle(genes)
        for r1_id in genes:
            if r1_id not in connected:
                if len(connected):
                    r2_id = choice(connected)
                    c.connect(r1_id, r2_id, innovation_indexer, weight=0.25)
                connected.append(r1_id)

        # Create attribute genes
        c.attribute_genes['hallway_alpha'] = AttributeGene(10, vmin=7, vmax=15)
        c.attribute_genes['hallway_decay'] = AttributeGene(.1, vmin=.05, vmax=.3)
        c.attribute_genes['fe_weight'] = AttributeGene(.3, vmin=.1, vmax=2)
        c.attribute_genes['concave_alpha'] = AttributeGene(40, vmin=20, vmax=60)
        return c
