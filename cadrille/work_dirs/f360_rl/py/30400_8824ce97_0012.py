import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,36,0))
r=w0.workplane(offset=-136/2).moveTo(0,0).cylinder(136,30).union(w0.sketch().circle(30).circle(22.5,mode='s').finalize().extrude(6)).union(w0.workplane(offset=64/2).cylinder(64,30))