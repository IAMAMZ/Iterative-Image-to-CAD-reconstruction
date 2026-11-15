import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,4))
r=w0.sketch().push([(-84,0)]).circle(16).circle(4.5,mode='s').push([(84,0)]).circle(16).rect(9,15.5,mode='s').finalize().extrude(-7)