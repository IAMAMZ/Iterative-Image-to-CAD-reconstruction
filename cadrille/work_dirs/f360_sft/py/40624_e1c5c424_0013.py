import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-3,0))
r=w0.sketch().segment((-100,-5),(-98,-12)).segment((98,-46)).segment((100,-38)).close().assemble().reset().face(w0.sketch().segment((-98,-3),(98,38)).segment((100,45)).segment((-98,0)).close().assemble()).finalize().extrude(6)