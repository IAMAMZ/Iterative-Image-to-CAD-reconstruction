import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,23,0))
r=w0.sketch().circle(100).circle(89,mode='s').circle(74).circle(61.5,mode='s').finalize().extrude(-46.5).union(w0.workplane(offset=-8/2).box(1.5,1.5,4.5))