import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,17,0))
r=w0.sketch().segment((-91,-62),(-90,-62)).arc((-89,12),(-32,58)).segment((-47,62)).arc((-94,7),(-91,-62)).assemble().reset().face(w0.sketch().arc((16,37),(31,34),(50,31)).segment((100,31.5)).segment((100,37)).segment((20.5,37.5)).close().assemble()).finalize().extrude(-33.5)