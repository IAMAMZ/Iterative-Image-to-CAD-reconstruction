import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-0))
r=w0.workplane(offset=1.5/2).box(118.5,200,1.5).union(w0.workplane(offset=1/2).box(11.5,18.5,1))