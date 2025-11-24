from __future__ import annotations

import os
from heuristics import insertion, route_first_cluster_second, savings

INSTANCE_DIR = "vrp_instances"
INSTANCE_FILES = [f"instance{k}.vrp" for k in range(1, 9)]

RESULTS_DIR = "results"
CSV_PATH = os.path.join(RESULTS_DIR, "heuristics_results.csv")
LATEX_PATH = os.path.join(RESULTS_DIR, "heuristics_table.tex")


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    rows = [] 

    for fname in INSTANCE_FILES:
        inst_path = os.path.join(INSTANCE_DIR, fname)
        if not os.path.exists(inst_path):
            print(f"[AVISO] {inst_path} não existe, pulando.")
            continue

        print(f"\n=== {fname} ===")

        sol_ins = insertion(inst_path)
        sol_rfcs = route_first_cluster_second(inst_path)
        sol_sav = savings(inst_path)

        cost_ins = sol_ins.distance()
        cost_rfcs = sol_rfcs.distance()
        cost_sav = sol_sav.distance()

        n_ins = len(sol_ins.routes())
        n_rfcs = len(sol_rfcs.routes())
        n_sav = len(sol_sav.routes())

        print(f"  Insertion               : dist = {cost_ins}  (rotas = {n_ins})")
        print(f"  Route-first-cluster-sec : dist = {cost_rfcs}  (rotas = {n_rfcs})")
        print(f"  Savings                 : dist = {cost_sav}  (rotas = {n_sav})")

        rows.append(
            (
                fname,
                cost_ins,
                n_ins,
                cost_rfcs,
                n_rfcs,
                cost_sav,
                n_sav,
            )
        )

    # ---------------- CSV ----------------
    with open(CSV_PATH, "w", encoding="utf-8") as f:
        f.write(
            "instance,"
            "insertion_cost,insertion_routes,"
            "rfcs_cost,rfcs_routes,"
            "savings_cost,savings_routes\n"
        )
        for (
            instance,
            cost_ins,
            n_ins,
            cost_rfcs,
            n_rfcs,
            cost_sav,
            n_sav,
        ) in rows:
            f.write(
                f"{instance},"
                f"{cost_ins},{n_ins},"
                f"{cost_rfcs},{n_rfcs},"
                f"{cost_sav},{n_sav}\n"
            )

    print(f"\n[INFO] Resultados salvos em: {CSV_PATH}")

    # ---------------- Tabela LaTeX ----------------
    with open(LATEX_PATH, "w", encoding="utf-8") as f:
        f.write("\\begin{table}[H]\n")
        f.write("\\centering\n")
        f.write("\\caption{Custo total (distância) e número de rotas das heurísticas construtivas.}\n")
        f.write("\\label{tab:heuristicas_construtivas}\n")
        f.write("\\begin{tabular}{lrrrrrr}\n")
        f.write("\\hline\n")
        f.write("Instância & "
                "Ins. dist & Ins. rotas & "
                "RFCS dist & RFCS rotas & "
                "Sav. dist & Sav. rotas \\\\\n")
        f.write("\\hline\n")

        for (
            instance,
            cost_ins,
            n_ins,
            cost_rfcs,
            n_rfcs,
            cost_sav,
            n_sav,
        ) in rows:
            f.write(
                f"{instance} & "
                f"{cost_ins} & {n_ins} & "
                f"{cost_rfcs} & {n_rfcs} & "
                f"{cost_sav} & {n_sav} \\\\\n"
            )

        f.write("\\hline\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table}\n")

    print(f"[INFO] Tabela LaTeX salva em: {LATEX_PATH}")


if __name__ == "__main__":
    main()
