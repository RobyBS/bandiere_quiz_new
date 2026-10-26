"""Contenitore Siporax "basso": h 10 mm, profilo con testate da 14 mm (come coperchio_esperimento).

Coperchio con uno strato in più (1.4 mm) e incastro più stretto (gioco 0.10).
Uso:  pip install trimesh manifold3d shapely networkx lxml  &&  python genera_basso.py
      python genera_basso.py 5   -> solo la scatola, 5 mm più alta (stesso coperchio)
"""
import sys

import trimesh
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

LATO_LUNGO = 65.0
LATO_CORTO = 11.0       # punta
TESTATA = 14.0          # testate ai capi del lato lungo
PROFONDITA = 39.0
ALTEZZA_TOT = 10.0      # scatola + coperchio chiuso
PARETE = 1.2
FONDO = 1.2
PIASTRA = 1.4           # piastra coperchio: 1.2 + uno strato da 0.2
FESSURA = 3.0
BARRETTA = 2.0
BORDO_PIENO = 2.2
GONNA_H = 3.0
GONNA_SP = 0.8
GIOCO = 0.10            # più stretto del solito 0.15

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


fori = griglia(inset(profilo, BORDO_PIENO))

EXTRA_H = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0

# Scatola
h_scatola = ALTEZZA_TOT - PIASTRA + EXTRA_H
esterno = estrudi(profilo, h_scatola)
cavita = estrudi(inset(profilo, PARETE), h_scatola + 1 - FONDO, FONDO)
scatola = trimesh.boolean.difference(
    [esterno, cavita, estrudi(fori, FONDO + 1.1, -1)], engine="manifold")

# Coperchio
interno = inset(profilo, PARETE + GIOCO)
anello = interno.difference(inset(interno, GONNA_SP))
coperchio = trimesh.boolean.union(
    [estrudi(profilo.difference(fori), PIASTRA), estrudi(anello, GONNA_H, PIASTRA)],
    engine="manifold")

if EXTRA_H:
    nome = f"scatola_basso_piu{EXTRA_H:g}mm"
    assert scatola.is_watertight
    scatola.export(f"{nome}.stl")
    scena = trimesh.Scene()
    scena.add_geometry(scatola, node_name="scatola", geom_name="scatola")
    scena.export(f"{nome}.3mf")
    vol = inset(profilo, PARETE).area * (h_scatola - FONDO) - anello.area * GONNA_H
    print(f"{nome}.3mf  {scatola.extents.round(2)} mm, vano utile ~{vol / 1000:.1f} cm3")
    sys.exit()

for nome, m in (("scatola_basso", scatola), ("coperchio_basso", coperchio)):
    assert m.is_watertight, nome
    m.export(f"{nome}.stl")
    print(f"{nome}.stl  {m.extents.round(2)} mm")

piatto = trimesh.Scene()
piatto.add_geometry(scatola, node_name="scatola", geom_name="scatola")
piatto.add_geometry(coperchio.copy().apply_translation([0, PROFONDITA + 8, 0]),
                    node_name="coperchio", geom_name="coperchio")
piatto.export("contenitore_siporax_basso.3mf")

vol = inset(profilo, PARETE).area * (h_scatola - FONDO) - anello.area * GONNA_H
print(f"contenitore_siporax_basso.3mf  vano utile ~{vol / 1000:.1f} cm3")
