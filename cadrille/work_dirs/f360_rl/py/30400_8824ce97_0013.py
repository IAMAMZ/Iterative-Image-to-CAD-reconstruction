import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,21,0))
r=w0.sketch().circle(100).circle(45,mode='s').finalize().extrude(-65.5).union(w0.sketch().circle(56).circle(45.5,mode='s').finalize().extrude(22)).union(w0.workplane(offset=2/2).box(1.5,1.5,1))