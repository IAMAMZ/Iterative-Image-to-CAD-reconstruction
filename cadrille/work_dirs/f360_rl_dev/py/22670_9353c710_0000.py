import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-73))
r=w0.sketch().circle(66.5).finalize().extrude(-27).union(w0.workplane(offset=173/2).cylinder(173,40))