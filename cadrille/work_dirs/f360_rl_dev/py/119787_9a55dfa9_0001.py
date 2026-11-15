import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-1))
r=w0.workplane(offset=4/2).box(133.5,200,4).union(w0.workplane(offset=1/2).box(129.5,186.5,1))