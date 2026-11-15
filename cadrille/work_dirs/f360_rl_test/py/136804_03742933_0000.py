import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,10,0))
r=w0.sketch().rect(200,100).circle(42.5,mode='s').finalize().extrude(-40).union(w0.workplane(offset=20/2).moveTo(0,0).box(6.5,75.5,20))