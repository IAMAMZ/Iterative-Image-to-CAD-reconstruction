import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,40,0))
r=w0.sketch().circle(40).circle(30,mode='s').finalize().extrude(-140).union(w0.workplane(offset=60/2).box(120,100,60)).union(w0.workplane(offset=60/2).box(1.5,1.5,6))