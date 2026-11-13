import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,13))
r=w0.workplane(offset=-25/2).moveTo(0,0).box(63,200,25).union(w0.workplane(offset=-19/2).box(9.5,186.5,19)).union(w0.workplane(offset=-17/2).box(9.5,17.5,17)).union(w0.workplane(offset=-7/2).box(9.5,17.5,6))