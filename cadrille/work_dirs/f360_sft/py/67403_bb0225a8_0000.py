import cadquery as cq
w0=cq.Workplane('YZ',origin=(-73,0,0))
r=w0.sketch().segment((-5,-7),(5,-7)).segment((5,7)).segment((-5,7)).segment((-5,3)).arc((-2,1),(-5,-1)).close().assemble().finalize().extrude(-27).union(w0.workplane(offset=173/2).cylinder(173,3))