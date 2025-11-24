from __future__ import annotations

import os
import time

from heuristics import insertion, route_first_cluster_second, savings

INSTANCE_DIR = "vrp_instances"
INSTANCE_FILES = [f"instance{k}.vrp" for k in range(1, 9)]

RESULTS_DIR = "results"
CSV_PATH = os.path.join(RESULTS_DIR, "heuristics_results.csv")
LATEX_PATH = os.path.join(RESULTS_DIR, "heuristics_table.tex")


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    rows = []  # instance, costs, routes, times

    for fname in INSTANCE_FILES:
        inst_path = os.path.join(INSTANCE_DIR, fname)
        if not os.path.exists(inst_path):
            print(f"[AVISO] {inst_path} não existe, pulando.")
            continue

        print(f"\n=== {fname} ===")

        # Insertion
        t0 = time.perf_counter()
        sol_ins = insertion(inst_path)
        t1 = time.perf_counter()

        cost_ins = sol_ins.distance()
        n_ins = len(sol_ins.routes())
        time_ins = t1 - t0

        # Route-first-cluster-second
        t0 = time.perf_counter()
        sol_rfcs = route_first_cluster_second(inst_path)
        t1 = time.perf_counter()

        cost_rfcs = sol_rfcs.distance()
        n_rfcs = len(sol_rfcs.routes())
        time_rfcs = t1 - t0

        # Savings
        t0 = time.perf_counter()
        sol_sav = savings(inst_path)
        t1 = time.perf_counter()

        cost_sav = sol_sav.distance()
        n_sav = len(sol_sav.routes())
        time_sav = t1 - t0

        print(
            f"  Insertion               : dist = {cost_ins:6d}, "
            f"rotas = {n_ins:2d}, tempo = {time_ins*1000:.2f} ms"
        )
        print(
            f"  Route-first-cluster-sec : dist = {cost_rfcs:6d}, "
            f"rotas = {n_rfcs:2d}, tempo = {time_rfcs*1000:.2f} ms"
        )
        print(
            f"  Savings                 : dist = {cost_sav:6d}, "
            f"rotas = {n_sav:2d}, tempo = {time_sav*1000:.2f} ms"
        )

        rows.append(
            (
                fname,
                cost_ins,
                n_ins,
                time_ins,
                cost_rfcs,
                n_rfcs,
                time_rfcs,
                cost_sav,
                n_sav,
                time_sav,
            )
        )

    # ---------- CSV ----------
    with open(CSV_PATH, "w", encoding="utf-8") as f:
        f.write(
            "instance,"
            "insertion_cost,insertion_routes,insertion_time,"
            "rfcs_cost,rfcs_routes,rfcs_time,"
            "savings_cost,savings_routes,savings_time\n"
        )
        for (
            instance,
            cost_ins,
            n_ins,
            time_ins,
            cost_rfcs,
            n_rfcs,
            time_rfcs,
            cost_sav,
            n_sav,
            time_sav,
        ) in rows:
            f.write(
                f"{instance},"
                f"{cost_ins},{n_ins},{time_ins:.6f},"
                f"{cost_rfcs},{n_rfcs},{time_rfcs:.6f},"
                f"{cost_sav},{n_sav},{time_sav:.6f}\n"
            )

    print(f"\n[INFO] Resultados salvos em: {CSV_PATH}")

    # ---------- Tabela LaTeX ----------
    with open(LATEX_PATH, "w", encoding="utf-8") as f:
        f.write("\\begin{table}[H]\n")
        f.write("\\centering\n")
        f.write("\\caption{Custo total, número de rotas e tempo (s) das heurísticas construtivas.}\n")
        f.write("\\label{tab:heuristicas_construtivas}\n")
        f.write("\\begin{tabular}{lrrrrrrrrr}\n")
        f.write("\\hline\n")
        f.write("Instância & "
                "Ins. dist & Ins. rotas & Ins. tempo & "
                "RFCS dist & RFCS rotas & RFCS tempo & "
                "Sav. dist & Sav. rotas & Sav. tempo \\\\\n")
        f.write("\\hline\n")

        for (
            instance,
            cost_ins,
            n_ins,
            time_ins,
            cost_rfcs,
            n_rfcs,
            time_rfcs,
            cost_sav,
            n_sav,
            time_sav,
        ) in rows:
            f.write(
                f"{instance} & "
                f"{cost_ins} & {n_ins} & {time_ins:.4f} & "
                f"{cost_rfcs} & {n_rfcs} & {time_rfcs:.4f} & "
                f"{cost_sav} & {n_sav} & {time_sav:.4f} \\\\\n"
            )

        f.write("\\hline\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table}\n")

    print(f"[INFO] Tabela LaTeX salva em: {LATEX_PATH}")


if __name__ == "__main__":
    main()
