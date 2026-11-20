import cadquery as cq
w0=cq.Workplane('YZ',origin=(26,0,0))
w1=cq.Workplane('ZX',origin=(0,-94,0))
r=w0.sketch().segment((-78,-78),(78,-100)).arc((90,-96),(94,-83)).segment((94,-14)).segment((92,-8)).segment((-78,100)).close().assemble().finalize().extrude(-51.5).union(w1.workplane(offset=19/2).moveTo(77,-0).cylinder(19,4.5)).union(w1.workplane(offset=7/2).moveTo(77,-0.5).box(6,1.5,1))