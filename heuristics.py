from __future__ import annotations
import math
from typing import List

from pyvrp import read, Solution


def _euclidean(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return math.hypot(dx, dy)


def basic_data(instance_path: str):
    """
    Lê a instância com pyvrp.read() e extrai informações básicas:
    - coordenadas do depósito e clientes
    - demanda de cada cliente
    - capacidade do veículo (primeira dimensão)
    """
    data = read(instance_path)

    clients = data.clients()
    depots = data.depots()
    if not depots:
        raise ValueError("Instância sem depósito.")

    depot = depots[0]

    # Capacidade do primeiro tipo de veículo, primeira dimensão de carga
    vtype = data.vehicle_type(0)
    capacity = vtype.capacity[0] if vtype.capacity else float("inf")

    depot_coord = (depot.x, depot.y)
    client_coords = [(c.x, c.y) for c in clients]
    client_demands = [c.delivery[0] if c.delivery else 0 for c in clients]

    return data, depot_coord, client_coords, client_demands, capacity


def insertion(instance_path: str) -> Solution:
    """
    Constrói uma solução inicial para o PyVRP usando Cheapest Insertion.

    - Primeiro gera uma ordem global de clientes (rota única).
    - Depois faz um split ingênuo dessa rota em várias rotas,
      respeitando o máximo que der a capacidade do 1º tipo de veículo.
    """
    data, depot_coord, client_coords, client_demands, capacity = basic_data(
        instance_path
    )
    num_clients = len(client_coords)

    unvisited = set(range(num_clients))

    # começa pelo cliente mais próximo do depósito
    first = min(unvisited, key=lambda j: _euclidean(depot_coord, client_coords[j]))
    route = [first]
    unvisited.remove(first)

    # cheapest insertion
    while unvisited:
        best_pos = None
        best_client = None
        best_increase = float("inf")

        for client in unvisited:
            prev_coord = depot_coord
            for pos in range(len(route) + 1):
                next_coord = depot_coord if pos == len(route) else client_coords[route[pos]]
                increase = (
                    _euclidean(prev_coord, client_coords[client])
                    + _euclidean(client_coords[client], next_coord)
                    - _euclidean(prev_coord, next_coord)
                )

                if increase < best_increase:
                    best_increase = increase
                    best_pos = pos
                    best_client = client

                if pos < len(route):
                    prev_coord = client_coords[route[pos]]

        route.insert(best_pos, best_client)
        unvisited.remove(best_client)

    # split por capacidade
    routes: List[List[int]] = []
    current_route: List[int] = []
    current_load = 0

    for client in route:
        demand = client_demands[client]
        if current_route and current_load + demand > capacity:
            routes.append(current_route)
            current_route = []
            current_load = 0

        current_route.append(client)
        current_load += demand

    if current_route:
        routes.append(current_route)

    return Solution(data, routes)

def route_first_cluster_second(instance_path: str) -> Solution:
    """
    Route-first, cluster-second:

    1. Constrói um 'giant tour' (TSP) que visita todos os clientes uma vez,
       usando nearest neighbour nas coordenadas (x, y).
    2. Faz o split do tour em rotas viáveis em capacidade.
    """
    data, depot_coord, client_coords, client_demands, capacity = basic_data(
        instance_path
    )
    num_clients = len(client_coords)

    # Giant tour via nearest neighbour
    unvisited = set(range(num_clients))
    tour: List[int] = []

    # começa pelo cliente mais próximo do depósito
    current = min(unvisited, key=lambda j: _euclidean(depot_coord, client_coords[j]))
    tour.append(current)
    unvisited.remove(current)

    while unvisited:
        cur_coord = client_coords[current]
        next_client = min(unvisited, key=lambda j: _euclidean(cur_coord, client_coords[j]))
        tour.append(next_client)
        unvisited.remove(next_client)
        current = next_client

    # Split do giant tour por capacidade
    routes: List[List[int]] = []
    current_route: List[int] = []
    current_load = 0

    for client in tour:
        demand = client_demands[client]

        if current_route and current_load + demand > capacity:
            routes.append(current_route)
            current_route = []
            current_load = 0

        current_route.append(client)
        current_load += demand

    if current_route:
        routes.append(current_route)

    # Garantia fraca pra não estourar num_vehicles:
    max_vehicles = data.num_vehicles
    if len(routes) > max_vehicles:
        merged = []
        for r in routes[max_vehicles - 1:]:
            merged.extend(r)
        routes = routes[: max_vehicles - 1] + [merged]

    return Solution(data, routes)

def savings(instance_path: str) -> Solution:
    """
    Representação:
      - clientes são índices 0..n_clients-1 (como em data.clients()).
      - cada rota é uma lista de clientes (depósito é implícito).

    Passos:
      1. Cria uma rota para cada cliente: [i].
      2. Calcula os savings s_ij = c(0,i) + c(0,j) - c(i,j).
      3. Ordena os pares (i,j) por saving decrescente.
      4. Percorre essa lista tentando unir rotas em que i e j estejam nas extremidades
         e a soma das demandas caiba na capacidade.
    """
    data, depot_coord, client_coords, client_demands, capacity = basic_data(
        instance_path
    )
    num_clients = len(client_coords)

    # 1) Pré-cálculo de distâncias: depósito–cliente e cliente–cliente
    d0 = [
        _euclidean(depot_coord, client_coords[i]) for i in range(num_clients)
    ]

    d_cc = [[0.0] * num_clients for _ in range(num_clients)]
    for i in range(num_clients):
        for j in range(i + 1, num_clients):
            dij = _euclidean(client_coords[i], client_coords[j])
            d_cc[i][j] = d_cc[j][i] = dij

    # 2) Savings s_ij = c(0,i) + c(0,j) - c(i,j), i < j
    savings_list: List[tuple[float, int, int]] = []
    for i in range(num_clients):
        for j in range(i + 1, num_clients):
            s_ij = d0[i] + d0[j] - d_cc[i][j]
            savings_list.append((s_ij, i, j))

    # Ordena savings em ordem decrescente
    savings_list.sort(key=lambda x: x[0], reverse=True)

    # 3) Rotas iniciais: uma rota por cliente
    routes: List[List[int]] = [[i] for i in range(num_clients)]
    route_loads: List[float] = [client_demands[i] for i in range(num_clients)]

    # client_route[c] = índice da rota em que o cliente c está
    client_route: List[int] = list(range(num_clients))

    # Checagem: demanda de cliente não pode ser maior que capacidade
    for c, dem in enumerate(client_demands):
        if dem > capacity:
            raise ValueError(
                f"Cliente {c} tem demanda {dem} maior que capacidade {capacity}."
            )

    # 4) Laço principal de união de rotas
    for s_ij, i, j in savings_list:
        ri = client_route[i]
        rj = client_route[j]

        # já estão na mesma rota -> não faz nada
        if ri == rj:
            continue

        route_i = routes[ri]
        route_j = routes[rj]

        # rota já foi esvaziada em merge anterior
        if not route_i or not route_j:
            continue

        load_i = route_loads[ri]
        load_j = route_loads[rj]

        # capacidade não pode estourar
        if load_i + load_j > capacity:
            continue

        # i e j precisam estar nas extremidades de suas rotas
        i_first = (route_i[0] == i)
        i_last = (route_i[-1] == i)
        j_first = (route_j[0] == j)
        j_last = (route_j[-1] == j)

        if not ((i_first or i_last) and (j_first or j_last)):
            # um deles está "no meio" da rota -> não unimos
            continue

        # Decide orientação para juntar as rotas, garantindo que i e j fiquem adjacentes na rota resultante.
        if i_last and j_first:
            new_route = route_i + route_j
        elif i_first and j_last:
            new_route = route_j + route_i
        elif i_first and j_first:
            new_route = list(reversed(route_i)) + route_j
        elif i_last and j_last:
            new_route = route_i + list(reversed(route_j))
        else:
            continue

        # merge: ri recebe a rota unida, rj é esvaziada
        routes[ri] = new_route
        routes[rj] = []
        route_loads[ri] = load_i + load_j
        route_loads[rj] = 0

        # Atualiza o mapeamento cliente -> rota
        for c in route_j:
            client_route[c] = ri

    # 5) Limpa rotas vazias e ajusta número de veículos
    final_routes = [r for r in routes if r]

    max_vehicles = data.num_vehicles
    if max_vehicles > 0 and len(final_routes) > max_vehicles:
        merged: List[int] = []
        for r in final_routes[max_vehicles - 1 :]:
            merged.extend(r)
        final_routes = final_routes[: max_vehicles - 1] + [merged]

    return Solution(data, final_routes)