"""Genera STL e 3MF del contenitore esagonale (trapezio con angoli smussati) per Siporax (scatola + coperchio a pressione).

Uso:  pip install trimesh manifold3d shapely networkx lxml  &&  python genera_stl.py
Tutte le misure sono in mm: modificare i parametri qui sotto e rilanciare.
"""
import trimesh
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

# --- Parametri ---------------------------------------------------------------
LATO_LUNGO = 65.0       # base maggiore del trapezio
LATO_CORTO = 11.0       # punta parallela al lato lungo (larghezza)
TESTATA = 13.0          # le due testate ai capi del lato lungo
PROFONDITA = 38.0       # dal lato lungo alla punta
ALTEZZA_TOT = 35.0      # scatola + coperchio chiuso
PARETE = 1.2            # spessore pareti laterali (3 perimetri con ugello 0.4)
FONDO = 1.2             # spessore fondo e piastra del coperchio
FESSURA = 3.0           # larghezza feritoie (< 5 mm così il Siporax 8x5 non passa)
BARRETTA = 2.0          # larghezza delle barrette tra le feritoie
BORDO_PIENO = 2.2       # fascia piena perimetrale prima delle feritoie
GONNA_H = 3.0           # altezza del bordino del coperchio che entra nella scatola
GONNA_SP = 0.8          # spessore del bordino
GIOCO = 0.15            # gioco per l'incastro (aumentare a 0.2-0.25 se troppo duro)

# --- Geometria ---------------------------------------------------------------
dx = (LATO_LUNGO - LATO_CORTO) / 2
trapezio = Polygon([(0, 0), (LATO_LUNGO, 0), (LATO_LUNGO, TESTATA),
                    (LATO_LUNGO - dx, PROFONDITA), (dx, PROFONDITA), (0, TESTATA)])


def inset(poly, d):
    return poly.buffer(-d, join_style="mitre")


def griglia(contorno):
    """Feritoie parallele alla profondità, ritagliate dentro `contorno`."""
    minx, miny, maxx, maxy = contorno.bounds
    passo = FESSURA + BARRETTA
    n = int((maxx - minx + BARRETTA) // passo)
    x0 = minx + ((maxx - minx) - (n * passo - BARRETTA)) / 2
    strisce = [box(x0 + i * passo, miny - 1, x0 + i * passo + FESSURA, maxy + 1)
               for i in range(n)]
    fori = unary_union(strisce).intersection(contorno)
    # scarta frammenti troppo piccoli vicino agli angoli acuti
    parti = getattr(fori, "geoms", [fori])
    return unary_union([p for p in parti if p.area > FESSURA * 2])


def estrudi(poly, h, z=0.0):
    parti = getattr(poly, "geoms", [poly])
    m = trimesh.util.concatenate([trimesh.creation.extrude_polygon(p, h) for p in parti])
    m.apply_translation([0, 0, z])
    return m


def piastra_forata(h):
    return estrudi(trapezio.difference(griglia(inset(trapezio, BORDO_PIENO))), h)


# Scatola: prisma esagonale a pareti lisce con fondo forato
h_scatola = ALTEZZA_TOT - FONDO
esterno = estrudi(trapezio, h_scatola)
cavita = estrudi(inset(trapezio, PARETE), h_scatola + 1 - FONDO, FONDO)
fori_fondo = estrudi(griglia(inset(trapezio, BORDO_PIENO)), FONDO + 1.1, -1)
scatola = trimesh.boolean.difference([esterno, cavita, fori_fondo], engine="manifold")

# Coperchio: piastra forata + bordino che entra a pressione nella scatola
interno = inset(trapezio, PARETE + GIOCO)
gonna = estrudi(interno.difference(inset(interno, GONNA_SP)), GONNA_H, FONDO)
coperchio = trimesh.boolean.union([piastra_forata(FONDO), gonna], engine="manifold")

for nome, m in (("scatola", scatola), ("coperchio", coperchio)):
    assert m.is_watertight, nome
    m.export(f"{nome}_v3.stl")
    print(f"{nome}_v3.stl  {m.extents.round(2)} mm, volume {m.volume / 1000:.1f} cm3")

# 3MF con i due pezzi affiancati sul piatto, già orientati per la stampa
piatto = trimesh.Scene()
piatto.add_geometry(scatola, node_name="scatola", geom_name="scatola")
piatto.add_geometry(coperchio.copy().apply_translation([0, PROFONDITA + 8, 0]),
                    node_name="coperchio", geom_name="coperchio")
piatto.export("contenitore_siporax_v3.3mf")
print("contenitore_siporax_v3.3mf")

cav = trimesh.boolean.intersection(
    [cavita, estrudi(box(-5, -5, 80, 50), h_scatola - FONDO, FONDO)], engine="manifold")
anello = interno.difference(inset(interno, GONNA_SP)).area * GONNA_H
print(f"volume utile interno ~{(cav.volume - anello) / 1000:.1f} cm3")
