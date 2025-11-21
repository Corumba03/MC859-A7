# utils.py
from pyvrp import read, Solution, GeneticAlgorithm, RandomNumberGenerator, PopulationParams, SolveParams
from pyvrp.solve import solve as pyvrp_solve

def run_pyvrp(instance_path, stop, seed, initial_solution=None, intensify: bool = True, diversify: bool = True):
    """Solve instance using PyVRP.

    Parameters
    - instance_path: path to VRPLIB instance
    - stop: a pyvrp.stop.StoppingCriterion (e.g., MaxRuntime)
    - seed: RNG seed
    - initial_solution: optional `pyvrp.Solution` to use as single initial solution
    - intensify: if False, disables route-level intensification (route_ops=[])
    - diversify: if False, reduces diversity influence (population lb/ub diversity -> 0.0)
    """
    rng = RandomNumberGenerator(seed=seed)
    instance = read(instance_path)

    # Configure population parameters
    if not diversify:
        population_params = PopulationParams(lb_diversity=0.0, ub_diversity=0.1)  # Ensure valid bounds
    else:
        population_params = PopulationParams()

    # Configure solver parameters 
    if not intensify:
        route_ops = []
        params = SolveParams(population=population_params, route_ops=route_ops)
    else:
        params = SolveParams(population=population_params)
        
    # Prepare initial solutions: either use provided or generate a small pool
    init = [Solution.make_random(instance, rng) for _ in range(25)] if initial_solution is None else [initial_solution]

    # If no explicit initial_solution was provided, use the high-level solve()
    # which builds and manages the population automatically and respects SolveParams.
    if initial_solution is None:
        return pyvrp_solve(instance, stop, seed=seed, params=params)

    # If an explicit initial solution is given, construct the GeneticAlgorithm
    # with our initial solutions and provided params. GeneticAlgorithm accepts
    # a `params` argument; if that API changes, falling back to the high-level
    # solve() is an alternative (but solve() doesn't accept explicit initials).
    algo = GeneticAlgorithm(instance, initial_solutions=init, params=params)
    return algo.run(stop)