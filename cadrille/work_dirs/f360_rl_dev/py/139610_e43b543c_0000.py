import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,50))
r=w0.workplane(offset=-100/2).moveTo(0,0).box(200,200,100).union(w0.workplane(offset=-50/2).box(192.5,186.5,50))