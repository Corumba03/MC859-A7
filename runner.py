import concurrent.futures
import os
import random
import time
import numpy as np
from pyvrp.stop import MaxRuntime
from pyvrp.Statistics import Statistics
from pyvrp import read, RandomNumberGenerator
from utils import run_pyvrp
from heuristics import insertion, route_first_cluster_second, savings

# Utility function
def _run_single_execution(instance_path: str, constructive_heuristic: function, seed: int, time_limit: int, target_value):
    """Worker executed in a separate process: loads the instance, sets seeds, and runs the algorithm."""

    # Generates an initial solution
    initial_solution = constructive_heuristic(instance_path)

    # Run the solver
    result = run_pyvrp(
        instance_path=instance_path,
        stop=MaxRuntime(time_limit),
        seed=seed,
        initial_solution=initial_solution,
    )

    # Extract time_to_target
    time_to_target = None
    for runtime, datum in zip(result.stats.runtimes, result.stats.feas_stats):
        if datum.best_cost <= target_value:
            time_to_target = runtime
            break

    # Return results
    return (
        instance_path,
        "PyVRP",
        seed,
        target_value,
        time_to_target if time_to_target is not None else float("inf"),
        result.cost(),
        sum(result.stats.runtimes)
    )

if __name__ == '__main__':
    TTT_PLOT_CONFIG = {
        'in/instance-05.txt': 1100,
        'in/instance-10.txt': 4000,
        'in/instance-15.txt': 8000,
    }

    # Experiment parameters
    NUM_EXECUTIONS = 50
    TIME_LIMIT_SECONDS = 30 * 60  # 10 minutes per execution
    OUTPUT_FILE = 'ttt_plot_results.csv'

    with open(OUTPUT_FILE, 'w') as f:
        # Write the CSV header
        f.write("instance,algorithm,execution_seed,target_value,time_to_target,final_solution_value,total_time\n")

        for instance_file, target_value in TTT_PLOT_CONFIG.items():
            print(f"\n--- Processing Instance: {instance_file} (Target: {target_value}) ---")

            # Create tasks for all seeds
            tasks = [
                (instance_file, seed, TIME_LIMIT_SECONDS, target_value)
                for seed in range(NUM_EXECUTIONS)
            ]

            max_workers = max(min(NUM_EXECUTIONS, os.cpu_count()) - 2, 1)

            # Execute in parallel and collect results; write to CSV in the main process
            with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(_run_single_execution, *t): t[2] for t in tasks}
                completed = 0
                for fut in concurrent.futures.as_completed(futures):
                    completed += 1
                    try:
                        (inst_name, alg, seed, target, t_to_target, sol_val, tot_time) = fut.result()
                    except Exception as e:
                        print(f"\n    [{time.strftime('%H:%M')}] Error in execution for seed {futures[fut]}: {e}")
                        continue

                    # Save results (serialized in the main process)
                    f.write(
                        f"{inst_name},"
                        f"{alg},"
                        f"{seed},"
                        f"{target},"
                        f"{t_to_target:.4f},"
                        f"{sol_val:.4f},"
                        f"{tot_time:.4f}\n"
                    )

                    print(f"\r     [{time.strftime('%H:%M')}] Executions completed: {completed}/{NUM_EXECUTIONS}...", end="")

                print(f"\n[{time.strftime('%H:%M')}]...Completed.")

    print(f"\n     [{time.strftime('%H:%M')}] Experiment finished! Results saved in '{OUTPUT_FILE}'.")
