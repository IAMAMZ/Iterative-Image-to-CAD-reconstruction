import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
w1=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().push([(0,-6)]).circle(94).circle(91,mode='s').finalize().extrude(18).union(w1.workplane(offset=-10/2).cylinder(10,4))