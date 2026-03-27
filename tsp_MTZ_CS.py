import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import openrouteservice
from docplex.mp.model import Model
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point, LineString
import contextily as ctx
import matplotlib.pyplot as plt
import pandas as pd

try:
    from cplex.callbacks import LazyConstraintCallback, UserCutCallback
except Exception:
    LazyConstraintCallback = None
    UserCutCallback = None

# --- CONFIGURAZIONE ---

api_key = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjYwM2NhMmFjM2ExYzI1MTJlZGY2YjNjZjJjMDIxNjQ3NGQ5ZjNkZmRkZWU0Nzc4NzNiMTc3MjIwIiwiaCI6Im11cm11cjY0In0='

if not api_key:
    raise RuntimeError("Missing ORS_API_KEY environment variable")


# --- DEFINIZIONE LOCATION ---
base_locations = [
    {"name": "Bastione Saint Remy", "coords": (39.2155, 9.1165)},
    {"name": "Anfiteatro Romano", "coords": (39.2238, 9.1098)},
    {"name": "Orto Botanico", "coords": (39.2230, 9.1080)},
    {"name": "Santuario di Bonaria", "coords": (39.2088, 9.1252)},
    {"name": "Parco Monte Urpinu", "coords": (39.2215, 9.1350)},
    {"name": "Parco Monte Claro", "coords": (39.2365, 9.1180)},
    {"name": "Mercato San Benedetto", "coords": (39.2250, 9.1235)},
    {"name": "Castello di San Michele", "coords": (39.2450, 9.1074)},
    {"name": "Stazione Treni Cagliari", "coords": (39.2148, 9.1095)},
    {"name": "Porto di Cagliari", "coords": (39.2110, 9.1110)},
    {"name": "Fiera della Sardegna", "coords": (39.2075, 9.1290)},
    {"name": "Stadio Unipol Domus", "coords": (39.2015, 9.1430)},
    {"name": "Parco Molentargius", "coords": (39.2200, 9.1550)},
    {"name": "Poetto - 1a Fermata", "coords": (39.1950, 9.1580)},
    {"name": "Poetto - 6a Fermata", "coords": (39.2208, 9.1876)},
    {"name": "Ospedale Marino", "coords": (39.2137, 9.1748)},
    {"name": "Faro Sant'Elia", "coords": (39.1846, 9.1476)},
    {"name": "Castello San Michele", "coords": (39.2420, 9.1050)},
    {"name": "Parco Terramaini", "coords": (39.2450, 9.1350)},
    {"name": "C.C. Santa Gilla", "coords": (39.2300, 9.0950)},
    {"name": "Aeroporto Elmas (P)", "coords": (39.2520, 9.0560)},
    {"name": "Comune di Elmas", "coords": (39.2680, 9.0450)},
    {"name": "Assemini Centro", "coords": (39.2880, 9.0050)},
    {"name": "Decathlon Cagliari", "coords": (39.2750, 9.0650)},
    {"name": "Sestu - Corte del Sole", "coords": (39.3050, 9.0950)},
    {"name": "Sestu Centro", "coords": (39.3000, 9.0900)},
    {"name": "Policlinico (Ingresso)", "coords": (39.2600, 9.1200)},
    {"name": "Cantine Monserrato", "coords": (39.2550, 9.1450)},
    {"name": "Deposito (Via S. Paolo)", "coords": (39.263557, 9.076127)},
    {"name": "Palazzo Delle Scienze", "coords": (39.222562, 9.114185)},
    {"name": "Facoltà Ingegneria", "coords": (39.229741, 9.108604)},
    {"name": "Osp. Santissima Trinità", "coords": (39.235543, 9.108285)},
    {"name": "Osp. Brotzu", "coords": (39.248497, 9.108608)},
    {"name": "Osp. Businco", "coords": (39.245257, 9.114284)},
    {"name": "Cittadella Universitaria", "coords": (39.270027, 9.124389)},
    {"name": "Selargius Centro", "coords": (39.2550, 9.1650)},
    {"name": "Selargius P. Lineare", "coords": (39.2500, 9.1600)},
    {"name": "Quartucciu Centro", "coords": (39.2520, 9.1750)},
    {"name": "C.C. Le Vele", "coords": (39.2450, 9.1602)},
    {"name": "Quartu Viale Colombo", "coords": (39.2300, 9.1950)},
    {"name": "Quartu S. Elena", "coords": (39.2400, 9.1980)},
    {"name": "Quartu Pitz'e Serra", "coords": (39.2450, 9.2100)},
    {"name": "Margine Rosso", "coords": (39.2287, 9.2186)},
    {"name": "Foxi", "coords": (39.2210, 9.2415)},
    {"name": "Flumini di Quartu", "coords": (39.2162, 9.2843)},
    {"name": "Barracca Manna", "coords": (39.2550, 9.1300)},
    {"name": "Is Corrias", "coords": (39.2650, 9.1400)},
    {"name": "Pirri Piazza Italia", "coords": (39.2450, 9.1300)},
    {"name": "Piazza Yenne", "coords": (39.2175, 9.1135)},
    {"name": "Mercato Via Quirra", "coords": (39.2389, 9.1057)},
    {"name": "Spiaggia di Giorgino", "coords": (39.2124, 9.0910)},
    {"name": "Teatro Lirico", "coords": (39.2280, 9.1250)},
    {"name": "Tribunale", "coords": (39.2220, 9.1280)},
    {"name" : "Chiesa del SS.Redentore", "coords": (39.2585, 9.1387)},  
    {"name": "Villa di Tigellio", "coords": (39.2210, 9.1050)},
    {"name": "Grotta della Vipera", "coords": (39.2250, 9.0980)},
    {"name": "Necropoli Tuvixeddu", "coords": (39.2280, 9.1020)}
]

all_locations_raw = base_locations[:50] 

locations = []
for idx, loc in enumerate(all_locations_raw):
    locations.append({
        "name": loc["name"],
        "id": idx,
        "coords": loc["coords"]
    })

n = len(locations)
cities = [i for i in range(n)]
arcs = [(i, j) for i in cities for j in cities if i != j]

print(f"--- Configurazione ---")
print(f"Totale Nodi: {n} (Limitato a 50 per compatibilità API Free)")


def extract_kpis(mdl: Model) -> Dict[str, Any]:
    """Extracts solver KPIs from docplex solve_details."""
    sd = getattr(mdl, 'solve_details', None)
    if sd is None:
        return {}
    return {
        'status': getattr(sd, 'status', None),
        'time': getattr(sd, 'time', None),
        'deterministic_time': getattr(sd, 'deterministic_time', None),
        'best_bound': getattr(sd, 'best_bound', None),
        'mip_relative_gap': getattr(sd, 'mip_relative_gap', None),
        'nb_nodes_processed': getattr(sd, 'nb_nodes_processed', None),
        'nb_iterations': getattr(sd, 'nb_iterations', None),
    }


def _build_subtour_cut_indices(comp: List[int], cities: List[int], arc_to_index: Dict[Tuple[int, int], int]) -> List[int]:
    """Builds variable indices for a cut-set constraint for a given component."""
    idxs: List[int] = []
    comp_set = set(comp)
    for u in comp:
        for v in cities:
            if v not in comp_set and u != v:
                idxs.append(arc_to_index[(u, v)])
    return idxs


def solve_cutset_with_callbacks(dist_matrix, dur_matrix, locations, log_output: bool = False):
    """Solves TSP with cut-set formulation using CPLEX lazy/user cuts if available."""
    print("\n" + "=" * 80)
    print("CUT SET (MIP) CON LAZY/USER CUTS")
    print("=" * 80)

    results = {
        'integer_solution': None,
        'time': 0,
        'kpis': {},
        'final_edges': None,
        'final_time': 0,
        'used_callbacks': False,
        'fallback_reason': None,
    }

    t0 = time.time()
    mdl = Model('TSP_CutSet_Callbacks')
    x = mdl.binary_var_dict(arcs, name='x')
    mdl.minimize(mdl.sum(dist_matrix[i][j] * x[(i, j)] for i, j in arcs))
    for i in cities:
        mdl.add_constraint(mdl.sum(x[(i, j)] for j in cities if i != j) == 1)
        mdl.add_constraint(mdl.sum(x[(j, i)] for j in cities if i != j) == 1)

    if LazyConstraintCallback is None or UserCutCallback is None:
        results['fallback_reason'] = 'CPLEX callbacks not available in this environment.'
        while True:
            sol = mdl.solve(log_output=log_output)
            results['kpis'] = extract_kpis(mdl)
            if not sol:
                break
            x_vals_int = {a: x[a].solution_value for a in arcs}
            G_int = nx.DiGraph()
            for (u, v), val in x_vals_int.items():
                if val > 0.9:
                    G_int.add_edge(u, v)
            comps_int = list(nx.strongly_connected_components(G_int))
            if len(comps_int) == 1:
                results['integer_solution'] = sol.objective_value
                ordered_edges = []
                curr = 0
                visited = 0
                while visited < n:
                    for j in cities:
                        if j != curr and x[(curr, j)].solution_value > 0.9:
                            ordered_edges.append((curr, j))
                            results['final_time'] += dur_matrix[curr][j]
                            curr = j
                            visited += 1
                            break
                results['final_edges'] = ordered_edges
                break
            for comp in comps_int:
                if len(comp) < n and len(comp) >= 2:
                    cut_expr = mdl.sum(x[(u, v)] for u in comp for v in cities if v not in comp)
                    mdl.add_constraint(cut_expr >= 1)

        results['time'] = time.time() - t0
        return results

    arc_list = list(arcs)
    arc_to_var = {a: x[a] for a in arc_list}
    arc_to_index: Dict[Tuple[int, int], int] = {}
    for a in arc_list:
        try:
            arc_to_index[a] = arc_to_var[a].get_index()
        except Exception:
            arc_to_index[a] = arc_to_var[a]._index

    class _SubtourLazy(LazyConstraintCallback):
        """Adds violated subtour elimination constraints at integer solutions."""

        def __call__(self):
            vals = self.get_values([arc_to_index[a] for a in arc_list])
            G_int = nx.DiGraph()
            for (u, v), val in zip(arc_list, vals):
                if val > 0.5:
                    G_int.add_edge(u, v)
            comps_int = list(nx.strongly_connected_components(G_int))
            if len(comps_int) <= 1:
                return
            for comp in comps_int:
                if len(comp) < n and len(comp) >= 2:
                    comp_list = list(comp)
                    idxs = _build_subtour_cut_indices(comp_list, cities, arc_to_index)
                    if not idxs:
                        continue
                    self.add((idxs, [1.0] * len(idxs)), 'G', 1.0)

    class _SubtourUserCut(UserCutCallback):
        """Adds violated subtour elimination constraints at fractional solutions."""

        def __call__(self):
            vals = self.get_values([arc_to_index[a] for a in arc_list])
            G_supp = nx.DiGraph()
            for (u, v), val in zip(arc_list, vals):
                if val > 0.001:
                    G_supp.add_edge(u, v, weight=val)
            comps = list(nx.strongly_connected_components(G_supp))
            violated = [c for c in comps if len(c) < n and len(c) >= 2]
            if not violated:
                return
            for comp in violated:
                comp_list = list(comp)
                idxs = _build_subtour_cut_indices(comp_list, cities, arc_to_index)
                if not idxs:
                    continue
                s = 0.0
                idx_set = set(idxs)
                for (u, v), val in zip(arc_list, vals):
                    if arc_to_index[(u, v)] in idx_set:
                        s += val
                if s < 1.0 - 1e-6:
                    self.add((idxs, [1.0] * len(idxs)), 'G', 1.0)

    mdl.get_cplex().register_callback(_SubtourLazy)
    mdl.get_cplex().register_callback(_SubtourUserCut)
    results['used_callbacks'] = True
    sol = mdl.solve(log_output=log_output)
    results['time'] = time.time() - t0
    results['kpis'] = extract_kpis(mdl)
    if sol:
        results['integer_solution'] = sol.objective_value
        ordered_edges = []
        curr = 0
        visited = 0
        while visited < n:
            for j in cities:
                if j != curr and x[(curr, j)].solution_value > 0.9:
                    ordered_edges.append((curr, j))
                    results['final_time'] += dur_matrix[curr][j]
                    curr = j
                    visited += 1
                    break
        results['final_edges'] = ordered_edges
    return results

# --- FUNZIONI DI VISUALIZZAZIONE ---

def save_table_img(df: pd.DataFrame, title: str, filename: str) -> None:
    """Save a pandas DataFrame as a PNG table with readable formatting."""
    df_render = format_table_for_rendering(df)

    nrows, ncols = df_render.shape
    # Heuristic sizing: wide enough for many columns, tall enough for rows
    fig_w = max(10, 2.2 * ncols)
    fig_h = max(3.5, 0.7 * (nrows + 1))

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis('off')
    ax.set_title(title, fontsize=22, pad=20, fontweight='bold')

    table = ax.table(
        cellText=df_render.values,
        colLabels=df_render.columns,
        cellLoc='center',
        loc='center'
    )

    table.auto_set_font_size(False)
    table.set_fontsize(14)
    table.scale(1.1, 1.8)

    # Auto-fit column widths (matplotlib >= 3.4 supports this helper)
    try:
        table.auto_set_column_width(col=list(range(ncols)))
    except Exception:
        pass

    fig.tight_layout()
    fig.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close(fig)

def format_table_for_rendering(df: pd.DataFrame) -> pd.DataFrame:
    # Format a DataFrame so that all values fit nicely in table cells.
    out = df.copy()

    def _is_nan(v: Any) -> bool:
        try:
            return v is None or (isinstance(v, float) and pd.isna(v))
        except Exception:
            return v is None

    def _fmt_int(v: Any) -> str:
        if _is_nan(v):
            return ""
        try:
            return str(int(v))
        except Exception:
            return str(v)

    def _fmt_float(v: Any, decimals: int) -> str:
        if _is_nan(v):
            return ""
        try:
            return f"{float(v):.{decimals}f}"
        except Exception:
            return str(v)

    if "Nodes" in out.columns:
        out["Nodes"] = out["Nodes"].map(_fmt_int)

    if "BestBound" in out.columns:
        out["BestBound"] = out["BestBound"].map(lambda v: _fmt_float(v, 2))

    if "MIPGap" in out.columns:
        out["MIPGap"] = out["MIPGap"].map(lambda v: _fmt_float(v, 6))

    return out

def plot_solution_on_map(client, locations, edges, total_time_min, total_distance_km, method_name):
    print(f"\n--- Generazione Mappa Percorsi ({method_name}) ---")
    points_geometry = [Point(loc["coords"][1], loc["coords"][0]) for loc in locations]
    points_gdf = gpd.GeoDataFrame(locations, geometry=points_geometry, crs="EPSG:4326")
    points_gdf = points_gdf.to_crs(epsg=3857)

    route_geometries = []
    print("Scaricamento geometrie stradali per la mappa (potrebbe richiedere tempo)...")
    
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
            time.sleep(0.5)
        except Exception as e:
            route_geometries.append(LineString([start_coords, end_coords]))

    routes_gdf = gpd.GeoDataFrame(geometry=route_geometries, crs="EPSG:4326")
    routes_gdf = routes_gdf.to_crs(epsg=3857)

    fig, ax = plt.subplots(1, 1, figsize=(15, 15))
    routes_gdf.plot(ax=ax, color='blue', linewidth=2, alpha=0.7, zorder=2, label='Percorso')
    points_gdf.plot(ax=ax, color='red', edgecolor='white', markersize=50, zorder=3)

    for idx, row in points_gdf.iterrows():
        if row['id'] <= 6 or row['id'] % 5 == 0:
            ax.text(row.geometry.x, row.geometry.y + 150, f"{row['id']}",
                    fontsize=8, color='black', weight='bold', ha='center', zorder=4,
                    bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=0.5))

    try:
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
    except Exception as e:
        print(f"Impossibile caricare la basemap: {e}")

    ax.set_axis_off()
    plt.title(f'Soluzione TSP - {method_name}\nDistanza: {total_distance_km:.2f} km - Tempo: {total_time_min:.0f} min')
    save_path = f"TSP_Map_{method_name.replace(' ', '_')}.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"--- Grafico salvato in: {save_path} ---")
    plt.close()

# --- FUNZIONI DI RISOLUZIONE ---

def solve_cutset_with_tracking(dist_matrix, dur_matrix, locations):
    """Risolve TSP con formulazione Cut Set in 3 Step."""
    print("\n" + "="*80)
    print("ANALISI FORMULAZIONE CUT SET (Branch & Cut)")
    print("="*80)

    results = {
        'step1_lp_bound': None, 'step1_time': 0,
        'step1_kpis': {},
        'step2_cuts_iterations': [], 'step2_time': 0,
        'step2_kpis_last': {},
        'step3_integer_solution': None, 'step3_time': 0,
        'step3_kpis': {},
        'final_edges': None, 'final_time': 0
    }

    # --- STEP 1: Rilassamento Lineare ---
    print("\n[STEP 1] Rilassamento Lineare (Problema di Assegnamento)")
    t0 = time.time()
    
    mdl_lp = Model('TSP_LP_Relaxation')
    x_lp = mdl_lp.continuous_var_dict(arcs, lb=0, ub=1, name='x')

    mdl_lp.minimize(mdl_lp.sum(dist_matrix[i][j] * x_lp[(i, j)] for i, j in arcs))

    for i in cities:
        mdl_lp.add_constraint(mdl_lp.sum(x_lp[(i, j)] for j in cities if i != j) == 1)
        mdl_lp.add_constraint(mdl_lp.sum(x_lp[(j, i)] for j in cities if i != j) == 1)

    sol_lp = mdl_lp.solve(log_output=False)
    results['step1_kpis'] = extract_kpis(mdl_lp)
    
    results['step1_time'] = time.time() - t0
    
    if sol_lp:
        results['step1_lp_bound'] = sol_lp.objective_value
        print(f">> Bound Iniziale: {sol_lp.objective_value:.2f} m | Tempo: {results['step1_time']:.4f} s")
    else:
        return results

    # --- STEP 2: Evoluzione del Bound con i Tagli ---
    print("\n[STEP 2] Aggiunta Tagli al Rilassamento Continuo")
    t0 = time.time()
    
    mdl_cuts = Model('TSP_LP_Cuts')
    x_cuts = mdl_cuts.continuous_var_dict(arcs, lb=0, ub=1, name='x')
    mdl_cuts.minimize(mdl_cuts.sum(dist_matrix[i][j] * x_cuts[(i, j)] for i, j in arcs))
    
    for i in cities:
        mdl_cuts.add_constraint(mdl_cuts.sum(x_cuts[(i, j)] for j in cities if i != j) == 1)
        mdl_cuts.add_constraint(mdl_cuts.sum(x_cuts[(j, i)] for j in cities if i != j) == 1)

    iteration = 0
    max_lp_cuts_iter = 15
    
    while iteration < max_lp_cuts_iter:
        sol = mdl_cuts.solve(log_output=False)
        if not sol: break

        results['step2_kpis_last'] = extract_kpis(mdl_cuts)
        
        current_bound = sol.objective_value
        x_vals = {a: x_cuts[a].solution_value for a in arcs}
        
        G_supp = nx.DiGraph()
        for (u, v), val in x_vals.items():
            if val > 0.01: G_supp.add_edge(u, v, weight=val)

        comps = list(nx.strongly_connected_components(G_supp))
        violated_comps = [c for c in comps if len(c) < n and len(c) >= 2]
        
        results['step2_cuts_iterations'].append({
            'iteration': iteration + 1,
            'bound': current_bound,
            'num_subtours': len(violated_comps)
        })
        
        print(f"   Iter {iteration+1}: Bound LP = {current_bound:.2f} m | Subtours: {len(violated_comps)}")

        if len(violated_comps) == 0: break
        
        for comp in violated_comps:
            cut_expr = mdl_cuts.sum(x_cuts[(u, v)] for u in comp for v in cities if v not in comp)
            mdl_cuts.add_constraint(cut_expr >= 1)
        
        iteration += 1

    results['step2_time'] = time.time() - t0
    print(f">> Tempo fase tagli LP: {results['step2_time']:.4f} s")

    # --- STEP 3: Soluzione Intera Finale ---
    print("\n[STEP 3] Soluzione Intera (Branch & Cut Finale)")
    t0 = time.time()
    
    mdl_int = Model('TSP_Integer')
    x_int = mdl_int.binary_var_dict(arcs, name='x')

    mdl_int.minimize(mdl_int.sum(dist_matrix[i][j] * x_int[(i, j)] for i, j in arcs))

    for i in cities:
        mdl_int.add_constraint(mdl_int.sum(x_int[(i, j)] for j in cities if i != j) == 1)
        mdl_int.add_constraint(mdl_int.sum(x_int[(j, i)] for j in cities if i != j) == 1)

    while True:
        sol_int = mdl_int.solve(log_output=False)
        if not sol_int: break

        results['step3_kpis'] = extract_kpis(mdl_int)
            
        x_vals_int = {a: x_int[a].solution_value for a in arcs}
        G_int = nx.DiGraph()
        for (u, v), val in x_vals_int.items():
            if val > 0.9: G_int.add_edge(u, v)
            
        comps_int = list(nx.strongly_connected_components(G_int))
        
        if len(comps_int) == 1:
            results['step3_integer_solution'] = sol_int.objective_value
            # Ricostruzione path
            ordered_edges = []
            curr = 0
            visited = 0
            while visited < n:
                for j in cities:
                    if j != curr and x_int[(curr, j)].solution_value > 0.9:
                        ordered_edges.append((curr, j))
                        results['final_time'] += dur_matrix[curr][j]
                        curr = j
                        visited += 1
                        break
            results['final_edges'] = ordered_edges
            break
        else:
            for comp in comps_int:
                if len(comp) < n:
                    cut_expr = mdl_int.sum(x_int[(u, v)] for u in comp for v in cities if v not in comp)
                    mdl_int.add_constraint(cut_expr >= 1)

    results['step3_time'] = time.time() - t0
    print(f">> Soluzione Ottima: {results['step3_integer_solution']:.2f} m | Tempo: {results['step3_time']:.4f} s")
    
    return results

def solve_mtz(dist_matrix, dur_matrix, locations):
    """Risolve TSP con formulazione MTZ + Timing."""
    print("\n" + "="*80)
    print("ANALISI FORMULAZIONE MTZ (Miller-Tucker-Zemlin)")
    print("="*80)

    results = {
        'continuous_relaxation': None, 'lp_time': 0,
        'lp_kpis': {},
        'integer_solution': None, 'int_time': 0,
        'int_kpis': {},
        'final_edges': None
    }

    # 1. Rilassamento Continuo MTZ
    print("\n[MTZ - Calcolo Rilassamento Continuo...]")
    t0 = time.time()
    
    mdl_mtz = Model('TSP_MTZ')
    x = mdl_mtz.continuous_var_dict(arcs, lb=0, ub=1, name='x')
    u = mdl_mtz.continuous_var_dict(cities, lb=0, ub=n-1, name='u')

    mdl_mtz.minimize(mdl_mtz.sum(dist_matrix[i][j] * x[(i, j)] for i, j in arcs))

    for i in cities:
        mdl_mtz.add_constraint(mdl_mtz.sum(x[(i, j)] for j in cities if i != j) == 1)
        mdl_mtz.add_constraint(mdl_mtz.sum(x[(j, i)] for j in cities if i != j) == 1)

    for i in cities[1:]:
        for j in cities[1:]:
            if i != j:
                mdl_mtz.add_constraint(u[i] - u[j] + n * x[(i, j)] <= n - 1)

    sol_lp = mdl_mtz.solve(log_output=False)
    results['lp_kpis'] = extract_kpis(mdl_mtz)
    results['lp_time'] = time.time() - t0
    
    if sol_lp:
        results['continuous_relaxation'] = sol_lp.objective_value
        print(f">> Bound MTZ (LP): {sol_lp.objective_value:.2f} m | Tempo: {results['lp_time']:.4f} s")

    # 2. Soluzione Intera MTZ
    print("\n[MTZ - Calcolo Soluzione Intera...]")
    t0 = time.time()
    
    mdl_mtz.clear_constraints()
    mdl_mtz_int = Model('TSP_MTZ_Int')
    x_int = mdl_mtz_int.binary_var_dict(arcs, name='x')
    u_int = mdl_mtz_int.continuous_var_dict(cities, lb=0, ub=n-1, name='u')
    
    mdl_mtz_int.minimize(mdl_mtz_int.sum(dist_matrix[i][j] * x_int[(i, j)] for i, j in arcs))
    
    for i in cities:
        mdl_mtz_int.add_constraint(mdl_mtz_int.sum(x_int[(i, j)] for j in cities if i != j) == 1)
        mdl_mtz_int.add_constraint(mdl_mtz_int.sum(x_int[(j, i)] for j in cities if i != j) == 1)
        
    for i in cities[1:]:
        for j in cities[1:]:
            if i != j:
                mdl_mtz_int.add_constraint(u_int[i] - u_int[j] + n * x_int[(i, j)] <= n - 1)
    
    mdl_mtz_int.set_time_limit(300) # 300 secondi max
    sol_int = mdl_mtz_int.solve(log_output=True)
    results['int_kpis'] = extract_kpis(mdl_mtz_int)
    
    results['int_time'] = time.time() - t0
    
    if sol_int:
        results['integer_solution'] = sol_int.objective_value
        print(f">> Soluzione Intera MTZ: {sol_int.objective_value:.2f} m | Tempo: {results['int_time']:.4f} s")
    else:
        print(f"Time limit o nessuna soluzione (Tempo: {results['int_time']:.4f} s)")

    return results

def generate_comparison_outputs(cutset, mtz):
    print("\n" + "="*80)
    print(f"{'GENERAZIONE TABELLE COMPARATIVE':^80}")
    print("="*80)
    
    data = []
    
    # CUT SET ROWS
    if cutset['step1_lp_bound']:
        k = cutset.get('step1_kpis', {})
        data.append({
            'Metodo': 'Cut Set',
            'Fase': '1. Rilassamento LP',
            'Bound (m)': f"{cutset['step1_lp_bound']:.2f}",
            'Tempo (s)': f"{cutset['step1_time']:.4f}",
            'Nodes': k.get('nb_nodes_processed', None),
            'BestBound': k.get('best_bound', None),
            'MIPGap': k.get('mip_relative_gap', None),
        })
    
    if cutset['step2_cuts_iterations']:
        last = cutset['step2_cuts_iterations'][-1]
        k = cutset.get('step2_kpis_last', {})
        data.append({
            'Metodo': 'Cut Set',
            'Fase': '2. Post-Tagli (LP)',
            'Bound (m)': f"{last['bound']:.2f}",
            'Tempo (s)': f"{cutset['step2_time']:.4f}",
            'Nodes': k.get('nb_nodes_processed', None),
            'BestBound': k.get('best_bound', None),
            'MIPGap': k.get('mip_relative_gap', None),
        })
        
    if cutset['step3_integer_solution']:
        k = cutset.get('step3_kpis', {})
        data.append({
            'Metodo': 'Cut Set',
            'Fase': '3. Ottimo Intero',
            'Bound (m)': f"{cutset['step3_integer_solution']:.2f}",
            'Tempo (s)': f"{cutset['step3_time']:.4f}",
            'Nodes': k.get('nb_nodes_processed', None),
            'BestBound': k.get('best_bound', None),
            'MIPGap': k.get('mip_relative_gap', None),
        })
        
    # MTZ ROWS
    if mtz['continuous_relaxation']:
        k = mtz.get('lp_kpis', {})
        data.append({
            'Metodo': 'MTZ',
            'Fase': 'Rilassamento LP',
            'Bound (m)': f"{mtz['continuous_relaxation']:.2f}",
            'Tempo (s)': f"{mtz['lp_time']:.4f}",
            'Nodes': k.get('nb_nodes_processed', None),
            'BestBound': k.get('best_bound', None),
            'MIPGap': k.get('mip_relative_gap', None),
        })
        
    if mtz['integer_solution']:
        k = mtz.get('int_kpis', {})
        data.append({
            'Metodo': 'MTZ',
            'Fase': 'Ottimo Intero',
            'Bound (m)': f"{mtz['integer_solution']:.2f}",
            'Tempo (s)': f"{mtz['int_time']:.4f}",
            'Nodes': k.get('nb_nodes_processed', None),
            'BestBound': k.get('best_bound', None),
            'MIPGap': k.get('mip_relative_gap', None),
        })
    else:
        k = mtz.get('int_kpis', {})
        data.append({
            'Metodo': 'MTZ',
            'Fase': 'Ottimo Intero',
            'Bound (m)': 'Timeout',
            'Tempo (s)': f"{mtz['int_time']:.4f}",
            'Nodes': k.get('nb_nodes_processed', None),
            'BestBound': k.get('best_bound', None),
            'MIPGap': k.get('mip_relative_gap', None),
        })
        
    df = pd.DataFrame(data)
    df_out = format_table_for_rendering(df)
    print(df_out.to_string(index=False))

    df_out.to_csv('Risultati_Confronto_CutSet_MTZ.csv', index=False)
    print("--- CSV salvato in: Risultati_Confronto_CutSet_MTZ.csv ---")
    
    # Salva PNG Tabella Principale
    save_table_img(df_out, "Confronto Cut-Set vs MTZ (Bound & Tempi)", "Tabella_Confronto_Risultati.png")
    
    # GAP ANALYSIS TABELLA
    opt = cutset['step3_integer_solution']
    gap_data = []
    
    if opt and mtz['continuous_relaxation']:
        gap = (opt - mtz['continuous_relaxation']) / opt * 100
        gap_data.append({'Metrica': 'GAP Iniziale MTZ', 'Valore': f"{gap:.2f}%"})
        
    if opt and cutset['step1_lp_bound']:
        gap = (opt - cutset['step1_lp_bound']) / opt * 100
        gap_data.append({'Metrica': 'GAP Iniziale Cut Set', 'Valore': f"{gap:.2f}%"})
        
    if opt and cutset['step2_cuts_iterations']:
        last_lp = cutset['step2_cuts_iterations'][-1]['bound']
        gap = (opt - last_lp) / opt * 100
        gap_data.append({'Metrica': 'GAP Cut Set (Post Tagli)', 'Valore': f"{gap:.2f}%"})
        
    df_gap = pd.DataFrame(gap_data)
    save_table_img(df_gap, "Analisi dei GAP (Efficienza Formulazione)", "Tabella_Gap_Analysis.png")


def generate_tree_kpi_table(cutset_tracking, cutset_callbacks, mtz):
    """Generates a KPI table focused on B&B tree size and solve effort."""
    rows = []

    k_cs = cutset_tracking.get('step3_kpis', {})
    rows.append({
        'Metodo': 'Cut Set (loop cuts)',
        'Nodes': k_cs.get('nb_nodes_processed', None),
        'BestBound': k_cs.get('best_bound', None),
        'MIPGap': k_cs.get('mip_relative_gap', None),
        'Tempo (s)': f"{cutset_tracking.get('step3_time', 0):.4f}",
    })

    if cutset_callbacks is not None:
        k_cb = cutset_callbacks.get('kpis', {})
        rows.append({
            'Metodo': 'Cut Set (lazy/user cuts)',
            'Nodes': k_cb.get('nb_nodes_processed', None),
            'BestBound': k_cb.get('best_bound', None),
            'MIPGap': k_cb.get('mip_relative_gap', None),
            'Tempo (s)': f"{cutset_callbacks.get('time', 0):.4f}",
        })

    k_mtz = mtz.get('int_kpis', {})
    rows.append({
        'Metodo': 'MTZ (MIP)',
        'Nodes': k_mtz.get('nb_nodes_processed', None),
        'BestBound': k_mtz.get('best_bound', None),
        'MIPGap': k_mtz.get('mip_relative_gap', None),
        'Tempo (s)': f"{mtz.get('int_time', 0):.4f}",
    })

    df = pd.DataFrame(rows)
    print("\n" + "=" * 80)
    print(f"{'KPI ALBERO BRANCH-AND-BOUND':^80}")
    print("=" * 80)
    print(df.to_string(index=False))
    df.to_csv('KPI_Albero_BranchAndBound.csv', index=False)
    print("--- CSV salvato in: KPI_Albero_BranchAndBound.csv ---")
    save_table_img(df, "KPI Albero Branch-and-Bound", "Tabella_KPI_Albero_BnB.png")

# --- MAIN ---

if __name__ == "__main__":
    if not api_key:
        print("ERRORE: Imposta la variabile d'ambiente ORS_API_KEY.")
        sys.exit(1)

    print("Calcolo matrici (Distanza e Tempo) tramite OpenRouteService...")
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
        print("Matrici ottenute con successo.\n")
    except Exception as e:
        print(f"Errore API: {e}")
        sys.exit(1)

    # 1. Esegui Cut Set Analysis
    res_cutset = solve_cutset_with_tracking(dist_matrix, dur_matrix, locations)

    # 1b. Esegui Cut Set con Lazy/User cuts (se disponibili)
    res_cutset_cb = solve_cutset_with_callbacks(dist_matrix, dur_matrix, locations, log_output=False)
    
    # 2. Esegui MTZ Analysis
    res_mtz = solve_mtz(dist_matrix, dur_matrix, locations)
    
    # 3. Tabelle e PNG
    generate_comparison_outputs(res_cutset, res_mtz)
    generate_tree_kpi_table(res_cutset, res_cutset_cb, res_mtz)
    
    # 4. Plot Mappa Finale
    if res_cutset['final_edges']:
        km = res_cutset['step3_integer_solution'] / 1000
        mins = res_cutset['final_time'] / 60
        plot_solution_on_map(client, locations, res_cutset['final_edges'], mins, km, "CutSet_Final_50_Nodes")
