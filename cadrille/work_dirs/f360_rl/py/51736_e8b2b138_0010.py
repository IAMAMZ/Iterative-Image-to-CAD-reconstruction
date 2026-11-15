import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,9,0))
r=w0.sketch().circle(100).circle(91,mode='s').finalize().extrude(-16.5).union(w0.workplane(offset=-13.5/2).cylinder(13.5,100)).union(w0.workplane(offset=-2/2).cylinder(2,9))