import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-8,0))
r=w0.sketch().segment((-100,52),(-80,11)).arc((-7,-19),(49,-50)).segment((100,-53.5)).segment((8,-8.5)).segment((-27,21)).segment((-49,14.5)).segment((-86,54.5)).close().assemble().finalize().extrude(13).union(w0.sketch().segment((32,-35),(85,-56)).segment((86,-54.5)).close().assemble().finalize().extrude(16))