import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,5))
r=w0.sketch().rect(122,200).rect(20,46,mode='s').push([(0,-63)]).circle(4,mode='s').push([(0,49)]).circle(4,mode='s').finalize().extrude(-11)