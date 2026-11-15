import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-33.5))
r=w0.workplane(offset=36/2).moveTo(-29.5,0).box(129.5,166.5,36).union(w0.sketch().segment((-100,-85),(15,-85.5)).arc((100,0),(15,85.5)).segment((-15.5,85.5)).segment((-100,85.5)).close().assemble().finalize().extrude(67))