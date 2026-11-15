import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,6,0))
r=w0.workplane(offset=-12/2).cylinder(12,96).union(w0.sketch().circle(100).finalize().extrude(-6))