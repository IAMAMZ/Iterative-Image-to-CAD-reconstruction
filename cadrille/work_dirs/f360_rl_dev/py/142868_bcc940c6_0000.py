import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().circle(27.5).circle(15.5,mode='s').finalize().extrude(-200).union(w0.workplane(offset=-13/2).cylinder(13,59)).union(w0.workplane(offset=-9/2).box(1.5,1.5,8))