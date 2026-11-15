import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,12))
r=w0.sketch().push([(0,-79)]).circle(21).circle(15,mode='s').push([(0,85)]).circle(15.5).circle(9,mode='s').finalize().extrude(-24)