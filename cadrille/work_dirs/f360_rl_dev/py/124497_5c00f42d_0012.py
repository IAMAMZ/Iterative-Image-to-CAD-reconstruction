import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,73))
w1=cq.Workplane('XY',origin=(0,0,-37))
r=w0.sketch().segment((-36,-25),(25,-25)).segment((25,-36)).segment((47,-35)).segment((47,-25)).segment((100,-25)).segment((100,6)).segment((68,6)).segment((67,0)).segment((-36,3)).close().assemble().finalize().extrude(-142.5).union(w0.workplane(offset=-36/2).moveTo(-69,7.5).cylinder(36,29)).union(w1.workplane(offset=-37/2).moveTo(-70,7).cylinder(37,29)).union(w1.workplane(offset=-33/2).moveTo(-70.5,-7).box(59.5,35,33))