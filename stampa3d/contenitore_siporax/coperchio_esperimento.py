"""Coperchio sperimentale: piastra 2 mm, bordino 5 mm, testate allungate di 3 mm verso il lato lungo.

Il bordino resta dimensionato per la scatola di genera_stl.py (contropezzo);
la piastra sporge di 3 mm oltre il lato lungo, piena, senza feritoie.
Uso:  pip install trimesh manifold3d shapely networkx lxml  &&  python coperchio_esperimento.py
"""
import trimesh
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

LATO_LUNGO = 65.0
LATO_CORTO = 11.0
PROFONDITA = 36.0       # della scatola (contropezzo)
ALLUNGO = 3.0           # testate allungate dalla parte del lato lungo: 11 -> 14
PIASTRA = 2.0
PARETE = 1.2            # parete della scatola su cui deve entrare il bordino
FESSURA = 3.0
BARRETTA = 2.0
BORDO_PIENO = 2.2
GONNA_H = 5.0
GONNA_SP = 0.8
GIOCO = 0.15

dx = (LATO_LUNGO - LATO_CORTO) / 2
scatola = Polygon([(0, 0), (LATO_LUNGO, 0), (LATO_LUNGO, LATO_CORTO),
                   (LATO_LUNGO - dx, PROFONDITA), (dx, PROFONDITA), (0, LATO_CORTO)])
piastra = Polygon([(0, -ALLUNGO), (LATO_LUNGO, -ALLUNGO), (LATO_LUNGO, LATO_CORTO),
                   (LATO_LUNGO - dx, PROFONDITA), (dx, PROFONDITA), (0, LATO_CORTO)])


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


lastra = estrudi(piastra.difference(griglia(inset(scatola, BORDO_PIENO))), PIASTRA)
interno = inset(scatola, PARETE + GIOCO)
gonna = estrudi(interno.difference(inset(interno, GONNA_SP)), GONNA_H, PIASTRA)
coperchio = trimesh.boolean.union([lastra, gonna], engine="manifold")
coperchio.apply_translation([0, ALLUNGO, 0])

assert coperchio.is_watertight
coperchio.export("coperchio_esperimento.stl")
scena = trimesh.Scene()
scena.add_geometry(coperchio, node_name="coperchio", geom_name="coperchio")
scena.export("coperchio_esperimento.3mf")
print(f"coperchio_esperimento  {coperchio.extents.round(2)} mm")
