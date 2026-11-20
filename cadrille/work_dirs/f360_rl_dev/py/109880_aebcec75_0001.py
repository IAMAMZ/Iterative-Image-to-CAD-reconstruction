import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,38))
r=w0.workplane(offset=-76/2).moveTo(0,0).box(172,200,76).union(w0.workplane(offset=-39/2).box(166.5,186.5,39))