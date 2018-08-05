import pickle

import networkx as nx

from floor_plans.genome import Genome
from floor_plans.config import Config
from floor_plans.indexer import Indexer, InnovationIndexer

from floor_plans.visualize import View
from floor_plans.floorplan import FloorPlan
from floor_plans.geometry import dist
from floor_plans import floorplan_statistics
from example import evaluate, spec, create_scores

from floor_plans.hallways import create_hallways
from floor_plans.hallway_smoothing import smooth

if __name__ == '__main__':
    n = 5
    
    innovation_indexer = InnovationIndexer(0)
    config = Config('config.txt')
    config.spec = spec
    
    for i in range(n):
        print(i)
        # genome = pickle.load(open('winner(dec31)/winner_school2.p'))
        genome = Genome.create(0, config, innovation_indexer)
        floor = FloorPlan.from_genome(genome, view=None)
