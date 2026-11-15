import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,9))
r=w0.sketch().segment((-52,-95),(-44,-100)).segment((44,-100)).segment((52,-95)).segment((51,95)).segment((44,100)).segment((-44,100)).segment((-52,97)).close().assemble().finalize().extrude(-18).union(w0.workplane(offset=-6/2).box(92.5,194.5,6))