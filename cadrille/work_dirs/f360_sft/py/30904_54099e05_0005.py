import cadquery as cq
w0=cq.Workplane('YZ',origin=(77,0,0))
w1=cq.Workplane('YZ',origin=(-90,0,0))
r=w0.workplane(offset=-177/2).moveTo(0,-53).cylinder(177,17).union(w0.sketch().arc((-38,-39),(0,-79),(38,-39)).segment((38,44)).arc((-1,79),(-38,44)).close().assemble().finalize().extrude(23)).union(w1.sketch().arc((-24,-60),(10,-77),(24,-42)).segment((24,59)).arc((-10,75),(-24,41)).close().assemble().finalize().extrude(-10))