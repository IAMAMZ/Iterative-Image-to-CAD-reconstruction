import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,58))
r=w0.workplane(offset=-158/2).cylinder(158,27.5).union(w0.sketch().circle(62).finalize().extrude(42))