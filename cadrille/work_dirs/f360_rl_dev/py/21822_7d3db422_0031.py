import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-15,0))
r=w0.workplane(offset=-85/2).cylinder(85,64.5).union(w0.sketch().circle(85.5).reset().face(w0.sketch().segment((-62,-2),(-26,-57)).segment((37,-50)).segment((62,2)).segment((26,57)).segment((-37,50)).close().assemble(),mode='s').finalize().extrude(115))