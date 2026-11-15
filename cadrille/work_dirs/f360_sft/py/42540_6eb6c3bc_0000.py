import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-1,0))
w1=cq.Workplane('YZ',origin=(-100,0,0))
r=w0.workplane(offset=80/2).moveTo(-37,0).cylinder(80,13).union(w1.sketch().segment((-79,-87),(29,-87)).segment((29,13)).arc((-7,26),(-30,57)).segment((-30,87)).segment((-79,87)).close().assemble().finalize().extrude(200))