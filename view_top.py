from __future__ import print_function
import sys, os
import pickle
import gzip

from floor_plans.visualize import View
from floor_plans.floorplan import FloorPlan

# path = '/home/simonlab/Dropbox/floor_plans/out/school_January_15_2017_17-24/winner_school_population2.p'
# path = '/home/simonlab/Dropbox/floor_plans/out/school_January_15_2017_15-53/winner_school_population2.p.gz'
if __name__ == '__main__':
    assert(len(sys.argv) == 2)
    path = sys.argv[1]



    out = os.path.join(os.path.dirname(path), 'others')
    if not os.path.exists(out):
        os.makedirs(out)

    population = pickle.load(gzip.open(path))
    genomes = population.statistics.best_unique_genomes(10)

    scale = 2
    bounds = (int(750.*scale), int(750.*scale))
    view = View(*bounds, scale=scale)#, save_path='/home/simonlab/Dropbox/floor_plans/tmp')

    for i, g in enumerate(genomes[1:]):
        floor = FloorPlan.from_genome(g, view=None, cache=True, firescapes=True)
        view.draw_floorplan(floor)
        save_path = os.path.join(out, ('rank%i.png'%(i+1)))
        view.save(save_path)