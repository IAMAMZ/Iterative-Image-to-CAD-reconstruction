import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,57,0))
r=w0.sketch().circle(65.5).circle(35.5,mode='s').finalize().extrude(-157).union(w0.sketch().circle(100).circle(36.5,mode='s').finalize().extrude(23)).union(w0.sketch().circle(63.5).circle(36.5,mode='s').finalize().extrude(42))