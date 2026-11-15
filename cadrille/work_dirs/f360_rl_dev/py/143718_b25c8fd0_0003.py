import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,56))
r=w0.workplane(offset=-156/2).cylinder(156,7.5).union(w0.workplane(offset=44/2).cylinder(44,5))