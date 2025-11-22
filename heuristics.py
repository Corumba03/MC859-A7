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