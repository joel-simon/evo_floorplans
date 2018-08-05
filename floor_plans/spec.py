import networkx as nx

class BuildingSpec(nx.Graph):
    """docstring for BuildingSpec"""
    def __init__(self, population):
        super(BuildingSpec, self).__init__()
        self.population = population
        self.name_to_spec = dict()
        self._next_id = 0
        self.variable_room_types = []

    def get_id(self):
        ID = self._next_id
        self._next_id += 1
        return ID

    def add_room(self, name, area, outside=False):
        ID = self.get_id()
        self.add_node(ID, name=name, area=area)
        self.name_to_spec[name] = {'area': area, 'ID': ID, 'outside': outside}
        return ID

    def add_requirement_by_name(self, name1, name2, rtype):
        assert(rtype in ['adjacent', 'near'])
        id1 = self.name_to_spec[name1]['ID']
        id2 = self.name_to_spec[name2]['ID']
        self.add_edge(id1, id2, type=rtype)

    def add_requirement(self, id1, id2, rtype):
        assert(rtype in ['adjacent', 'near'])
        self.add_edge(id1, id2, type=rtype)

    def add_variable_room(self, name, start_size):
        assert isinstance(name, str)
        assert isinstance(start_size, (int, float))
        self.variable_room_types.append((name, start_size))