import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-20,0))
r=w0.sketch().circle(100).finalize().extrude(10).union(w0.workplane(offset=20/2).moveTo(0,94).cylinder(20,3)).union(w0.sketch().circle(12).circle(9.5,mode='s').finalize().extrude(40))