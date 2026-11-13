import cadquery as cq
w0=cq.Workplane('YZ',origin=(62,0,0))
r=w0.workplane(offset=-124/2).cylinder(124,12).union(w0.sketch().arc((-98,-22),(0,-100),(98,-22)).close().assemble().reset().face(w0.sketch().segment((-98,22),(98,22)).arc((0,100),(-98,22)).assemble()).finalize().extrude(-25))