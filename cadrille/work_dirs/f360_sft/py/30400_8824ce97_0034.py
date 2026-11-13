import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-100,0))
r=w0.sketch().segment((-5,4),(5,4)).arc((0,5),(-5,4)).assemble().reset().face(w0.sketch().arc((5,-5),(5,-4),(6,-4)).arc((5,-2),(5,-1)).close().assemble()).finalize().extrude(200)