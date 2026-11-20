import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,43))
r=w0.workplane(offset=-86.5/2).moveTo(0,0).box(200,193.5,86).union(w0.workplane(offset=-57/2).box(192.5,190,57)).union(w0.workplane(offset=-19/2).box(186.5,182.5,19))