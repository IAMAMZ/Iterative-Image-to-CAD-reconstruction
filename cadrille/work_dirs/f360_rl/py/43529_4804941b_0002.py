import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-76,0))
r=w0.workplane(offset=-24/2).cylinder(24,63).union(w0.sketch().circle(45).finalize().extrude(121)).union(w0.sketch().circle(36.5).circle(26.5,mode='s').finalize().extrude(176))