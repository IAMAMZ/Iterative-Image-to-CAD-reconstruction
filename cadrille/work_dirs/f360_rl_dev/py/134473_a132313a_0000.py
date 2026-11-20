import cadquery as cq
w0=cq.Workplane('YZ',origin=(22,0,0))
r=w0.workplane(offset=-44/2).moveTo(-26.5,-0).box(16,100,44).union(w0.sketch().segment((-23,-49),(5,-49)).segment((5,-100)).segment((34.5,-100)).segment((35,100)).segment((5,100)).segment((5,49)).segment((-23,49)).close().assemble().finalize().extrude(-6))