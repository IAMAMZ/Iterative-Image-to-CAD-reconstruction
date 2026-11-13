import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,46,0))
r=w0.workplane(offset=-146/2).cylinder(146,30).union(w0.sketch().circle(31).circle(29,mode='s').finalize().extrude(-10)).union(w0.workplane(offset=54/2).cylinder(54,30))