import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-94,0))
r=w0.sketch().circle(46.5).circle(38.5,mode='s').finalize().extrude(-5).union(w0.workplane(offset=188/2).cylinder(188,61.5)).union(w0.workplane(offset=194/2).cylinder(194,10))