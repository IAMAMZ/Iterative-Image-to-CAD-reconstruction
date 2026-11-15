import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-22,0))
r=w0.sketch().circle(100).circle(48,mode='s').finalize().extrude(15).union(w0.sketch().circle(55.5).circle(22.5,mode='s').finalize().extrude(44))