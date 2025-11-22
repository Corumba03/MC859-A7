from __future__ import annotations
import math
from typing import List

from pyvrp import read, Solution


def _euclidean(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return math.hypot(dx, dy)


def build_insertion_order(instance_path: str) -> List[int]:
    """
    Constrói uma única rota (ordem de clientes) usando Cheapest Insertion,
    ignorando por enquanto capacidade e janelas de tempo.
    Retorna uma permutação dos índices de clientes [0 .. n_clients-1].
    """
    data = read(instance_path)
    clients = data.clients()
    depot = data.depots()[0]

    n = len(clients)

    # Coordenadas
    depot_coord = (depot.x, depot.y)
    client_coords = [(c.x, c.y) for c in clients]

    # Distâncias cliente–cliente e depósito–cliente
    d_cc = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = _euclidean(client_coords[i], client_coords[j])
            d_cc[i][j] = d_cc[j][i] = d

    d_dep = [_euclidean(depot_coord, client_coords[i]) for i in range(n)]

    # Inicialização da rota
    # Começa com o cliente mais perto do depósito
    first = min(range(n), key=lambda i: d_dep[i])
    route: List[int] = [first]
    remaining = set(range(n))
    remaining.remove(first)

    # Laço principal de inserção
    def route_cost(seq: List[int]) -> float:
        if not seq:
            return 0.0
        cost = d_dep[seq[0]] + d_dep[seq[-1]]
        for i in range(len(seq) - 1):
            cost += d_cc[seq[i]][seq[i + 1]]
        return cost

    while remaining:
        best_client = None
        best_pos = None
        best_delta = float("inf")

        current_cost = route_cost(route)

        for c in remaining:
            # tenta inserir c em todas as posições da rota
            for pos in range(len(route) + 1):
                new_route = route[:pos] + [c] + route[pos:]
                new_cost = route_cost(new_route)
                delta = new_cost - current_cost
                if delta < best_delta:
                    best_delta = delta
                    best_client = c
                    best_pos = pos

        # aplica melhor inserção encontrada
        route.insert(best_pos, best_client)
        remaining.remove(best_client)

    return route


def insertion(instance_path: str) -> Solution:
    """
    Constrói uma solução inicial para o PyVRP usando Cheapest Insertion.

    - Primeiro gera uma ordem global de clientes (rota única).
    - Depois faz um split ingênuo dessa rota em várias rotas,
      respeitando o máximo que der a capacidade do 1º tipo de veículo.
    """
    data = read(instance_path)
    order = build_insertion_order(instance_path)

    clients = data.clients()
    veh_type = data.vehicle_types()[0]
    num_vehicles = data.num_vehicles

    # capacidade em 1 dimensão (caso CVRP padrão);
    # se não houver nada definido, tratamos como capacidade infinita
    capacity = veh_type.capacity[0] if veh_type.capacity else math.inf

    routes: List[List[int]] = []
    current_route: List[int] = []
    current_load = 0

    for c_idx in order:
        demand = clients[c_idx].delivery[0] if clients[c_idx].delivery else 0

        # se colocar aqui estoura capacidade E ainda temos veículos sobrando,
        # fecha rota e começa outra
        if (
            current_route
            and current_load + demand > capacity
            and len(routes) + 1 < num_vehicles
        ):
            routes.append(current_route)
            current_route = [c_idx]
            current_load = demand
        else:
            current_route.append(c_idx)
            current_load += demand

    if current_route:
        routes.append(current_route)

    # Em último caso, se usamos mais veículos que o permitido,
    # junta tudo numa rota só (nunca pode passar de num_vehicles)
    if len(routes) > num_vehicles and num_vehicles > 0:
        merged: List[int] = [c for r in routes for c in r]
        routes = [merged]

    # routes é uma lista de listas de clientes; o Solution cuida do resto.
    return Solution(data, routes)
