from __future__ import print_function, division
import os
import pickle
import math
import sys
import gzip
from itertools import combinations
from datetime import datetime

from floor_plans import population, concave_hull
from floor_plans.floorplan import FloorPlan, UnconnectedGenomeException, InvalidContraintException
from floor_plans.math_util import mean, geometric_mean, weighted_geometric_mean
from floor_plans.visualize import View
from floor_plans.visualize_evolution import plot_stats,  plot_species
from floor_plans.config import Config
from floor_plans.parallel import ParallelEvaluator
from floor_plans import statistics
from floor_plans.spec import BuildingSpec
from floor_plans import floorplan_statistics
from pyvoro import voroplusplus
import networkx as nx

import sys
sys.dont_write_bytecode = True

spec = BuildingSpec(population=500)
preks = [
    spec.add_room('PK', 1041),
    spec.add_room('PK', 1050),
    spec.add_room('PK', 1079),
]
ks = [
    spec.add_room('K', 1090),
    spec.add_room('K', 1105),
    spec.add_room('K', 1093),
    spec.add_room('K', 1110),
    spec.add_room('K', 1105),
]
firsts = [
    spec.add_room('1', 872),
    spec.add_room('1', 882),
    spec.add_room('1', 877),
    spec.add_room('1', 879),
    spec.add_room('1', 883),
]
seconds = [
    spec.add_room('2', 872),
    spec.add_room('2', 882),
    spec.add_room('2', 877),
    spec.add_room('2', 879),
    spec.add_room('2', 883),
]

spec.add_room('team', 328)
spec.add_room('work', 503)
spec.add_room('janitorial', 181)
spec.add_room('title 1', 526)
spec.add_room('tutoring', 106+222+113+111+112)
spec.add_room('conference', 251)
spec.add_room('resource', 872)

spec.add_room('none1', 1104)
spec.add_room('autism', 835)
spec.add_room('proj', 942)
spec.add_room('music', area=900)
spec.add_room('art', area=1076)
spec.add_room('life skills', area=825)

spec.add_room('storage1', area=227)
spec.add_room('OT/PT', area=503)
spec.add_room('faculty', area=482)

gym = spec.add_room('gym', area=6993)
stage = spec.add_room('stage', area=915)
cafeteria = spec.add_room('cafeteria', area=3811)

kitchen = spec.add_room('kitchen', area=1701)
spec.add_room('boiler', area=1316)
spec.add_room('library', area=2637)
spec.add_room('administration', area=3303)
spec.add_room('administration', area=3281)

spec.add_room('none2', area=659)
spec.add_room('electrical', area=365)
spec.add_room('computer lab', area=636)

spec.add_room('bldg storage', area=731)
spec.add_room('recycle', area=229)
spec.add_room('custodial', area=330)

spec.add_room('playground', area=10000, outside=True)


spec.add_variable_room('toilet', 200)
for i in range(1):
    spec.add_room('toilet', area=200)

spec.add_variable_room('empty', 800)
for i in range(3):
    spec.add_room('empty', area=800)

spec.add_requirement(gym, stage, 'adjacent')
spec.add_requirement(cafeteria, kitchen, 'adjacent')

# def ratio_score(a, b):
#     if a == 0:
#         return 0
#     r = (b / a)
#     return 1.0 / (1.0 + math.exp(-4 * (r-1)))

def ratio_score(a, b):
    if a == 0:
        return 0
    x = (b / a)
    return 2 * math.atan(x) / (math.pi)

def target_score(a, b):
    if a == 0:
        return 0
    x = (b / a)
    return min(1, 4 * math.atan(x) / (math.pi))

weights = {
    # 'hallway': 1,
    'walluse': 1,
    # 'walking': 1,
    # 'cluster': 1,
    # 'toilets': 1,
    # 'toilet_load': 1,

    # 'surface_area': 2,
    # 'window_area': 2,
    # 'fire_escape': 1,
}

def create_scores(floor):
    baseline = {
        'hallway_area': 9932.7,
        'outside_wall_length': 1714.6,
        'total_wall_length': 7513.3,
        'average_walking_distance': 16112.2648558,
        'average_cluster_distance': 57.30,
        'toilet_dist': 18.2139872386,
        'fire_escape_dist': 75.79661,
        'toilet_load': 0.293694891984,
        'window_area': 0.280051487067,
    }
    scores = {
        'hallway': ratio_score(floor.stats['ha'], baseline['hallway_area']),
        'walluse': ratio_score(floor.stats['wl'], baseline['total_wall_length']),
        'surface': ratio_score(floor.stats['ol'], baseline['outside_wall_length']),
        'walking': ratio_score(floor.stats['wd'], baseline['average_walking_distance']),
        'cluster': ratio_score(floor.stats['cd'], baseline['average_cluster_distance']),
        'toilets': ratio_score(floor.stats['td'], baseline['toilet_dist']),
        'toilet_load': target_score(floor.stats['ta'], baseline['toilet_load']),

        'fire_escape': target_score(floor.stats['fe'], baseline['fire_escape_dist']),
        'surface_area': ratio_score(baseline['outside_wall_length'], floor.stats['ol']),
        'window_area': ratio_score(baseline['window_area'], floor.stats['wa']),
    }
    floor.scores = scores

    # print('hallway', round(floor.stats['ha'], 4), round(baseline['hallway_area'] / floor.stats['ha'],4))
    # print('walluse', round(floor.stats['wl'], 4), round(baseline['total_wall_length'] / floor.stats['wl'],4))
    # print('surface', round(floor.stats['ol'], 4), round(baseline['outside_wall_length'] / floor.stats['ol'],4))
    # print('walking', round(floor.stats['wd'], 4), round(baseline['average_walking_distance'] / floor.stats['wd'],4))
    # print('cluster', round(floor.stats['cd'], 4), round(baseline['average_cluster_distance'] / floor.stats['cd'],4))
    # print('toilets', round(floor.stats['td'], 4), round(baseline['toilet_dist'] / floor.stats['td'],4))
    # print('toilet_load', round(floor.stats['ta'], 4), round(baseline['toilet_load'] / floor.stats['ta'],4))

    # print('fire_escape', round(floor.stats['fe'], 4), round(baseline['fire_escape_dist'] / floor.stats['fe'],4))
    # print('window_area', floor.stats['wa'], round(baseline['window_area']/ floor.stats['wa'],4))

    # print('surface_area', baseline['outside_wall_length'], floor.stats['ol'])


def evaluate(genome):
    """ Return a score [0, 1]
    """

    try:
        firescapes = 'fire_escape' in weights
        floor = FloorPlan.from_genome(genome, firescapes=firescapes)

        if floor.area > 200000:# That inside-out issue
            sys.stdout.write('x')
            sys.stdout.flush()
            # pickle.dump(genome, open('debug/insideout_geneome.p', 'wb'))
            return (None, -999999)

        create_scores(floor)
        sys.stdout.write('.')
        sys.stdout.flush()
        S = []
        W = []
        return floor, -floor.stats['wl']
        # for name, weight in weights.items():
        #     S.append(floor.scores[name])
        #     W.append(weight)
        # return (floor, weighted_geometric_mean(S, W))

    except UnconnectedGenomeException as e:
        sys.stdout.write('1')
        sys.stdout.flush()
        return (None, -99999999)
    except concave_hull.InvalidHullException as e:
        sys.stdout.write('2')
        sys.stdout.flush()
        return (None, -99999999)
    except voroplusplus.VoronoiPlusPlusError as e:
        sys.stdout.write('3')
        sys.stdout.flush()
        # pickle.dump(genome, open('debug/voronoi_genome.p', 'wb'))
        return (None, -99999999)
    except InvalidContraintException as e:
        sys.stdout.write('4')
        sys.stdout.flush()
        # pickle.dump(genome, open('debug/constraint_genome.p', 'wb'))
        return (None, -99999999)
    except Exception as e:
        sys.stdout.write('E')
        sys.stdout.flush()
        print(e,  end='')
        return (None, -99999999)

    # import copy
    # copy.deepcopy(genome)

scale = 1.0
view = View(int(750.*scale), int(750.*scale), scale=scale)

def draw_genome(genome):
    # if genome.fitness > 0:
    floorplan = FloorPlan.from_genome(genome)
    view.draw_floorplan(floorplan)

def evaluate_all(genomes):
    for genome in genomes:
        floor, fitness = evaluate(genome)
        genome.fitness = fitness
        # genome.phenotype = floor

    best = max(genomes, key=lambda g: g.fitness)
    draw_genome(best)
    print()


if __name__ == '__main__':
    cores = 1
    generations = 100

    if len(sys.argv) > 1:
        out_root = sys.argv[1]
    else:
        out_root = os.getcwd()


    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.txt')
    config = Config(config_path)
    config.spec = spec

    pop = population.Population(config)

    if cores > 1:
        pe = ParallelEvaluator(cores, evaluate, draw=draw_genome)
        pop.run(pe.evaluate, generations)
        pe.pool.close()
    else:
        pop.run(evaluate_all, generations)
    print('\n')

    out_dir = os.path.join(out_root, "out/school_{:%B_%d_%Y_%H-%M}".format(datetime.now()))
    assert not os.path.exists(out_dir)
    os.makedirs(out_dir)
    with open(os.path.join(out_dir, 'weights.txt'), 'wb') as weights_file:
        weights_file.write(str(weights))

    winner = pop.statistics.best_genome()
    pickle.dump(winner, open(os.path.join(out_dir,'winner_genome.p'), 'wb'))
    pickle.dump(pop, gzip.open(os.path.join(out_dir,'winner_school_population2.p.gz'), 'wb'))

    floorplan = FloorPlan.from_genome(winner)

    print('best fitness', winner.fitness)


    view.draw_floorplan(floorplan)
    view.save(os.path.join(out_dir, 'school_winner.png'))
    plot_stats(pop.statistics, filename=os.path.join(out_dir, 'avg_fitness.svg'))
    plot_species(pop.statistics, filename=os.path.join(out_dir, 'speciation.svg'))

    with open(os.path.join(out_dir,'fitness.txt'), 'w') as fitness_file:
        fitness_file.write(str(winner.fitness))

    print('Number of evaluations: {0}'.format(pop.total_evaluations))
    # view.hold()
