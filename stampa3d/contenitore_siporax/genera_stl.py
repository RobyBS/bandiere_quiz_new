"""Genera gli STL del contenitore trapezoidale per Siporax (scatola + coperchio a pressione).

Uso:  pip install trimesh manifold3d shapely  &&  python genera_stl.py
Tutte le misure sono in mm: modificare i parametri qui sotto e rilanciare.
"""
import trimesh
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

# --- Parametri ---------------------------------------------------------------
LATO_LUNGO = 65.0       # base maggiore del trapezio
LATO_CORTO = 12.0       # base minore (parallela)
PROFONDITA = 26.5       # distanza tra le due basi (26.5 = lati obliqui a 45°)
ALTEZZA_TOT = 20.0      # scatola + coperchio chiuso
PARETE = 0.8            # spessore pareti laterali (2 perimetri con ugello 0.4)
FONDO = 1.0             # spessore fondo e piastra del coperchio
FESSURA = 3.0           # larghezza feritoie (< 5 mm così il Siporax 8x5 non passa)
BARRETTA = 2.0          # larghezza delle barrette tra le feritoie
BORDO_PIENO = 2.2       # fascia piena perimetrale prima delle feritoie
GONNA_H = 3.0           # altezza del bordino del coperchio che entra nella scatola
GONNA_SP = 0.8          # spessore del bordino
GIOCO = 0.15            # gioco per l'incastro (aumentare a 0.2-0.25 se troppo duro)

# --- Geometria ---------------------------------------------------------------
dx = (LATO_LUNGO - LATO_CORTO) / 2
trapezio = Polygon([(0, 0), (LATO_LUNGO, 0),
                    (LATO_LUNGO - dx, PROFONDITA), (dx, PROFONDITA)])


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
    m = trimesh.creation.extrude_polygon(poly, h)
    m.apply_translation([0, 0, z])
    return m


def piastra_forata(h):
    return estrudi(trapezio.difference(griglia(inset(trapezio, BORDO_PIENO))), h)


# Scatola: fondo forato + pareti piene
h_scatola = ALTEZZA_TOT - FONDO
pareti = estrudi(trapezio.difference(inset(trapezio, PARETE)), h_scatola - FONDO, FONDO)
scatola = trimesh.boolean.union([piastra_forata(FONDO), pareti], engine="manifold")

# Coperchio: piastra forata + bordino che entra a pressione nella scatola
interno = inset(trapezio, PARETE + GIOCO)
gonna = estrudi(interno.difference(inset(interno, GONNA_SP)), GONNA_H, FONDO)
coperchio = trimesh.boolean.union([piastra_forata(FONDO), gonna], engine="manifold")

for nome, m in (("scatola", scatola), ("coperchio", coperchio)):
    assert m.is_watertight, nome
    m.export(f"{nome}.stl")
    print(f"{nome}.stl  {m.extents.round(2)} mm, volume {m.volume / 1000:.1f} cm3")

vol_utile = inset(trapezio, PARETE).area * (h_scatola - FONDO - GONNA_H) / 1000
print(f"volume utile interno ~{vol_utile:.1f} cm3")
