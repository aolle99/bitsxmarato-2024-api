import osmnx as ox


def get_roads(lat, lon, distancia=1000, simplify_tolerance=None):
    # Descargar red de calles para conducir ('drive'), caminar ('walk') o bicicleta ('bike')
    G = ox.graph_from_point((lat, lon), dist=distancia, network_type='drive', simplify=True)

    # Convertir el grafo a GeoDataFrame sin nodos (solo las calles)
    calles = ox.graph_to_gdfs(G, nodes=False)

    if simplify_tolerance:
        # Simplificar las geometrías individuales si es necesario
        calles["geometry"] = calles["geometry"].simplify(tolerance=simplify_tolerance)

    return calles
