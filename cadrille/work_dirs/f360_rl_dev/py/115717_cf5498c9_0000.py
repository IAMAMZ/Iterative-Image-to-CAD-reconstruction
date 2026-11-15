import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.workplane(offset=200/2).box(90,5,200).union(w0.workplane(offset=200/2).box(7.5,3.5,10))