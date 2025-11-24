import sys
import openrouteservice
from docplex.mp.model import Model
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point, LineString
import contextily as ctx
import matplotlib.pyplot as plt

api_key = ''

locations = [
    {"name": "Deposito", "id": 0, "coords": (39.263557, 9.076127)},
    {"name": "Palazzo Delle Scienze", "id": 1, "coords": (39.222562, 9.114185)},
    {"name": "Ingegneria", "id": 2, "coords": (39.229741, 9.108604)},
    {"name": "Santissima Trinità", "id": 3, "coords": (39.235543, 9.108285)},
    {"name": "Brotzu", "id": 4, "coords": (39.248497, 9.108608)},
    {"name": "Businco", "id": 5, "coords": (39.245257, 9.114284)},
    {"name": "Cittadella Universitaria", "id": 6, "coords": (39.270027, 9.124389)}
]

n = len(locations)
nodes = [i for i in range(n)]
arcs = [(i, j) for i in nodes for j in nodes if i != j]

def plot_solution_on_map(client, locations, edges, total_time_min, total_distance_km, method_name):
    print(f"\n--- Generazione Mappa Percorsi ({method_name}) ---")
    
    points_geometry = [Point(loc["coords"][1], loc["coords"][0]) for loc in locations]
    points_gdf = gpd.GeoDataFrame(locations, geometry=points_geometry, crs="EPSG:4326")
    points_gdf = points_gdf.to_crs(epsg=3857)

    route_geometries = []
    print("Scaricamento geometrie stradali per la mappa...")
    
    for i, j in edges:
        try:
            start_coords = (locations[i]["coords"][1], locations[i]["coords"][0])
            end_coords = (locations[j]["coords"][1], locations[j]["coords"][0])
            
            route = client.directions(
                coordinates=[start_coords, end_coords], 
                profile='driving-car', 
                format='geojson'
            )
            coords = route['features'][0]['geometry']['coordinates']
            route_line = LineString(coords)
            route_geometries.append(route_line)
        except Exception as e:
            print(f"Avviso: fallback linea retta per arco {i}->{j}.")
            route_geometries.append(LineString([start_coords, end_coords]))
    
    routes_gdf = gpd.GeoDataFrame(geometry=route_geometries, crs="EPSG:4326")
    routes_gdf = routes_gdf.to_crs(epsg=3857)

    fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    routes_gdf.plot(ax=ax, color='blue', linewidth=3, alpha=0.7, zorder=2, label='Percorso')
    points_gdf.plot(ax=ax, color='orange', edgecolor='black', markersize=100, zorder=3)

    for idx, row in points_gdf.iterrows():
        ax.text(row.geometry.x, row.geometry.y + 150, f"{row['id']}. {row['name']}", 
                fontsize=9, color='black', weight='bold', ha='center', zorder=4,
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

    try:
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
    except Exception as e:
        print(f"Impossibile caricare la basemap: {e}")

    ax.set_axis_off()
    plt.title(f'Soluzione TSP Ottimizzata\nDistanza: {total_distance_km:.2f} km - Tempo stimato: {total_time_min:.0f} min')
    
    save_path = f"TSP_Map_Result.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"--- Grafico salvato in: {save_path} ---")
    plt.close()


# Funzione Principale
def main():
    print("Calcolo matrici (Distanza e Tempo) tramite OpenRouteService...")
    
    # Chiamata API per dati geografici
    try:
        client = openrouteservice.Client(key=api_key)
        coords_for_api = [[loc["coords"][1], loc["coords"][0]] for loc in locations]
        
        matrix_response = client.distance_matrix(
            locations=coords_for_api,
            profile='driving-car',
            metrics=['distance', 'duration'],
            units='m'
        )
        
        dist_matrix = matrix_response['distances']
        dur_matrix = matrix_response['durations']
        print("Matrici ottenute con successo.")

    except Exception as e:
        print(f"Errore API: {e}")
        sys.exit(1)

    # Inizializzazione Modello DocPlex
    mdl = Model('TSP_Real_Map')
    
    x = mdl.binary_var_dict(arcs, name='x') # Vettore variabili decisionali

    mdl.minimize(mdl.sum(dist_matrix[i][j] * x[(i, j)] for i, j in arcs)) # Funzione obiettivo con matrice distanza

    # Aggiunta vincoli visita singola per nodo
    for i in nodes:
        mdl.add_constraint(mdl.sum(x[(i, j)] for j in nodes if i != j) == 1)
        mdl.add_constraint(mdl.sum(x[(j, i)] for j in nodes if i != j) == 1)

    print("\nAvvio risoluzione CPLEX...")
    while True:
        sol = mdl.solve(log_output=False)
        if not sol:
            print("Problema infattibile."); sys.exit(1)
            
        x_vals = {a: x[a].solution_value for a in arcs} # Vettore risultato
        
        G_supp = nx.DiGraph()
        for (u, v), val in x_vals.items():
            if val > 0.9: G_supp.add_edge(u, v) # Aggiunta arco grafo di supporto
        
        comps = list(nx.strongly_connected_components(G_supp))
        
        if len(comps) == 1:
            print("Soluzione ottima e connessa trovata.")
            break
        else:
            print(f"Sottogiri trovati: {len(comps)}. Aggiunta vincoli di taglio...")
            for comp in comps:
                if len(comp) < n:
                    cut_expr = mdl.sum(x[(u, v)] for u in comp for v in nodes if v not in comp) # Aggiunta vincoli di taglio
                    mdl.add_constraint(cut_expr >= 1)

    final_dist = sol.objective_value
    final_time = 0

    ordered_edges = []
    curr = 0
    visited_count = 0
    while visited_count < n:
        for j in nodes:
            if j != curr and x[(curr, j)].solution_value > 0.9:
                ordered_edges.append((curr, j))
                final_time += dur_matrix[curr][j]
                curr = j
                visited_count += 1
                break

    dist_km = final_dist / 1000
    time_min = final_time / 60

    print("\n" + "="*80)
    print(f"{'DETTAGLIO ITINERARIO':^80}")
    print("="*80)
    print(f"{'Step':<5} | {'Località Partenza':<25} -> {'Località Arrivo':<25} | {'Km':<8} | {'Min':<8}")
    print("-" * 80)

    for idx, (u, v) in enumerate(ordered_edges, 1):
        nome_start = locations[u]['name']
        nome_end = locations[v]['name']
        d_km = dist_matrix[u][v] / 1000
        t_min = dur_matrix[u][v] / 60
        
        print(f"{idx:<5} | {nome_start:<25} -> {nome_end:<25} | {d_km:<8.2f} | {t_min:<8.0f}")

    print("-" * 80)
    print(f"TOTALI: {dist_km:.2f} km in circa {time_min:.0f} minuti")
    print("="*80 + "\n")

    plot_solution_on_map(
        client=client,
        locations=locations,
        edges=ordered_edges,
        total_time_min=time_min,
        total_distance_km=dist_km,
        method_name="CPLEX_BranchCut"
    )
    
    
if __name__ == "__main__":
    main()