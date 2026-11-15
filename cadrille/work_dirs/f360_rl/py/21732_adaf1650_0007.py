import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,14,0))
w1=cq.Workplane('ZX',origin=(0,11,0))
r=w0.sketch().push([(0,-85)]).circle(15).circle(7.5,mode='s').push([(0,85)]).circle(15).circle(7.5,mode='s').finalize().extrude(-28).union(w1.workplane(offset=-18/2).moveTo(0,-0).box(17,150.5,18)).union(w1.workplane(offset=-1/2).moveTo(9.5,97.5).box(1.5,1,1))