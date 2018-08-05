from multiprocessing import Pool


class ParallelEvaluator(object):
    def __init__(self, num_workers, eval_function, timeout=None, draw=None):
        '''
        eval_function should take one argument (a genome object) and return
        a single float (the genome's fitness).
        '''
        self.num_workers = num_workers
        self.eval_function = eval_function
        self.timeout = timeout
        self.pool = Pool(num_workers)
        self.draw = draw

    def evaluate(self, genomes):
        results = self.pool.map(self.eval_function, genomes)
        for genome, result in zip(genomes, results):
            floor, fitness = result
            genome.fitness = fitness
            genome.phenotype = floor

        best = max(genomes, key=lambda g: g.fitness)
        self.draw(best)