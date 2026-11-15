import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,36,0))
r=w0.sketch().circle(88.5).circle(35.5,mode='s').finalize().extrude(-71.5).union(w0.sketch().circle(100).circle(35.5,mode='s').finalize().extrude(-28.5))