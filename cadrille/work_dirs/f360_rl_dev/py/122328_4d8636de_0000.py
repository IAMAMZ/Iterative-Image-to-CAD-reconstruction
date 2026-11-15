import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,40))
r=w0.workplane(offset=-80/2).moveTo(0,0).box(200,180,80).union(w0.workplane(offset=-49/2).box(192.5,174.5,49))