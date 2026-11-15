import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,28))
r=w0.sketch().circle(75).circle(57.5,mode='s').finalize().extrude(-128).union(w0.sketch().circle(86.5).circle(58.5,mode='s').finalize().extrude(43)).union(w0.workplane(offset=72/2).cylinder(72,28))