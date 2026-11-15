import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,32))
r=w0.workplane(offset=-63.5/2).moveTo(0,0).box(200,156.5,63).union(w0.workplane(offset=-19/2).box(192.5,150.5,19))