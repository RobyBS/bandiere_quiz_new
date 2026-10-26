"""Contropezzo (scatola) per coperchio_esperimento: stesso profilo con testate da 14 mm.

Altezza totale da chiuso = scatola + piastra del coperchio (2 mm).
Uso:  pip install trimesh manifold3d shapely networkx lxml  &&  python contropezzo_esperimento.py
"""
import trimesh
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

LATO_LUNGO = 65.0
LATO_CORTO = 11.0       # punta
TESTATA = 14.0          # testate (11 + 3 come nel coperchio sperimentale)
PROFONDITA = 39.0
ALTEZZA_TOT = 12.0      # con il coperchio chiuso
PIASTRA_COPERCHIO = 2.0
GONNA_H = 5.0           # bordino del coperchio che entra nella scatola
PARETE = 1.2            # deve restare 1.2: il bordino del coperchio è calcolato su questa parete
FONDO = 1.2
FESSURA = 3.0
BARRETTA = 2.0
BORDO_PIENO = 2.2

dx = (LATO_LUNGO - LATO_CORTO) / 2
profilo = Polygon([(0, 0), (LATO_LUNGO, 0), (LATO_LUNGO, TESTATA),
                   (LATO_LUNGO - dx, PROFONDITA), (dx, PROFONDITA), (0, TESTATA)])


def inset(poly, d):
    return poly.buffer(-d, join_style="mitre")


def griglia(contorno):
    minx, miny, maxx, maxy = contorno.bounds
    passo = FESSURA + BARRETTA
    n = int((maxx - minx + BARRETTA) // passo)
    x0 = minx + ((maxx - minx) - (n * passo - BARRETTA)) / 2
    strisce = [box(x0 + i * passo, miny - 1, x0 + i * passo + FESSURA, maxy + 1)
               for i in range(n)]
    fori = unary_union(strisce).intersection(contorno)
    parti = getattr(fori, "geoms", [fori])
    return unary_union([p for p in parti if p.area > FESSURA * 2])


def estrudi(poly, h, z=0.0):
    parti = getattr(poly, "geoms", [poly])
    m = trimesh.util.concatenate([trimesh.creation.extrude_polygon(p, h) for p in parti])
    m.apply_translation([0, 0, z])
    return m


h_scatola = ALTEZZA_TOT - PIASTRA_COPERCHIO
assert h_scatola - FONDO > GONNA_H, "scatola troppo bassa per il bordino del coperchio"
esterno = estrudi(profilo, h_scatola)
cavita = estrudi(inset(profilo, PARETE), h_scatola + 1 - FONDO, FONDO)
fori_fondo = estrudi(griglia(inset(profilo, BORDO_PIENO)), FONDO + 1.1, -1)
scatola = trimesh.boolean.difference([esterno, cavita, fori_fondo], engine="manifold")

assert scatola.is_watertight
scatola.export("contropezzo_esperimento.stl")
scena = trimesh.Scene()
scena.add_geometry(scatola, node_name="contropezzo", geom_name="contropezzo")
scena.export("contropezzo_esperimento.3mf")
vol = inset(profilo, PARETE).area * (h_scatola - FONDO) / 1000
print(f"contropezzo_esperimento  {scatola.extents.round(2)} mm, vano interno ~{vol:.1f} cm3")
