import random

class AttributeGene(object):
    def __init__(self, value, vmin, vmax):
        self.value = value
        self.vmin = vmin
        self.vmax = vmax
        assert value >= vmin and value <= vmax

    def __str__(self):
        return 'AttributeGene(value={0}, vmin={1}, vmax={2})'.format(self.value, self.vmin, self.vmax)

    def get_child(self, other):
        """ Creates a new NodeGene randomly inheriting attributes from its parents."""
        value = (self.value + other.value)/2.0
        ng = AttributeGene(value, self.vmin, self.vmax)
        return ng

    def copy(self):
        return AttributeGene(self.ID, self.value, self.vmin, self.vmax)

    def mutate(self):
        mutation_power = (self.vmax - self.vmin)/2
        self.value += random.gauss(0, 1) * mutation_power
        self.value = max(self.vmin, min(self.vmax, self.value))


class NodeGene(object):
    def __init__(self, ID, size, name='', required=True):
        self.ID = ID
        self.min_size = 8
        self.size = max(self.min_size, size)
        self.name = name
        # A required node cannot be deleted.
        self.required = required

    def __str__(self):
        return 'NodeGene(id={0}, size={1}, requires={2})'.format(self.ID, self.size, self.required)

    def get_child(self, other):
        """ Creates a new NodeGene randomly inheriting attributes from its parents."""
        assert (self.ID == other.ID)
        if self.name != other.name:
            assert not(self.required or other.required)
            name = random.choice([self.name, other.name])
        else:
            name = self.name
        size = (self.size + other.size)/2.0
        ng = NodeGene(self.ID, size, name, self.required)
        return ng

    def copy(self):
        return NodeGene(self.ID, self.size, self.name, self.required)

    def mutate(self, config):
        node_mutation_power = 1#config.weight_mutation_power #TODO SWITCH
        self.size += random.gauss(0, 10) * node_mutation_power
        self.size = max(self.min_size, self.size)

class ConnectionGene(object):
    def __init__(self, innovation_id, in_node_id, out_node_id, weight, fixed, added=False):
        assert type(innovation_id) is int
        assert type(in_node_id) is int
        assert type(out_node_id) is int
        assert type(weight) is float
        assert type(fixed) is bool

        self.innovation_id = innovation_id
        self.in_node_id = in_node_id
        self.out_node_id = out_node_id
        self.weight = weight
        self.fixed = fixed
        self.added = added

    # Key for dictionaries, avoids two connections between the same nodes.
    key = property(lambda self: tuple(sorted((self.in_node_id, self.out_node_id))))

    def mutate(self, config):
        if self.fixed:
            return
        r = random.random
        if r() < config.prob_replace_weight:
            # Replace weight with a random value.
            self.weight = random.random()
        else:
            # Perturb weight.
            new_weight = self.weight + random.gauss(0, 1)# * config.weight_mutation_power
            self.weight = max(config.min_weight, min(config.max_weight, new_weight))


    def __str__(self):
        return 'ConnectionGene(in={0}, out={1}, weight={2}, fixed={3}, innov={4})'.format(
            self.in_node_id, self.out_node_id, self.weight, self.fixed, self.innovation_id)

    def __lt__(self, other):
        return self.innovation_id < other.innovation_id

    def split(self, innovation_indexer, node_id):
        """ Splits a connection, creating two new connections and disabling this one """
        innovation1 = innovation_indexer.get_innovation_id(self.in_node_id, node_id)
        new_conn1 = ConnectionGene(innovation1, self.in_node_id, node_id, 1.0, True)

        innovation2 = innovation_indexer.get_innovation_id(node_id, self.out_node_id)
        new_conn2 = ConnectionGene(innovation2, node_id, self.out_node_id, self.weight, True)

        return new_conn1, new_conn2

    def copy(self):
        return ConnectionGene(self.innovation_id, self.in_node_id, self.out_node_id, self.weight, self.fixed, self.added)

    def is_same_innov(self, other):
        return self.innovation_id == other.innovation_id

    def get_child(self, other):
        """ Creates a new ConnectionGene randomly inheriting attributes from its parents."""
        assert self.innovation_id == other.innovation_id
        cg = ConnectionGene(self.innovation_id, self.in_node_id, self.out_node_id,
                      random.choice((self.weight, other.weight)),
                      self.fixed, self.added)
        return cg
