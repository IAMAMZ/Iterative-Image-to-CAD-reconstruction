import cadquery as cq
w0=cq.Workplane('YZ',origin=(-12,0,0))
r=w0.sketch().segment((-14,-76),(15,-76)).segment((11,78)).arc((0,100),(-10,78)).close().assemble().finalize().extrude(11).union(w0.sketch().push([(0,-81)]).circle(19).circle(9,mode='s').finalize().extrude(24))