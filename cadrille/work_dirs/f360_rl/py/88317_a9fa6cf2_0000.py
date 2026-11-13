import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,9))
r=w0.sketch().push([(0,-6)]).circle(96).circle(92.5,mode='s').finalize().extrude(-18).union(w0.workplane(offset=-2/2).moveTo(0,96.5).box(4.5,7,2))