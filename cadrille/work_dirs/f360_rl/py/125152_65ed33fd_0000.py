import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,15,0))
r=w0.sketch().circle(100).circle(98,mode='s').finalize().extrude(-30).union(w0.sketch().circle(100).finalize().extrude(-14))