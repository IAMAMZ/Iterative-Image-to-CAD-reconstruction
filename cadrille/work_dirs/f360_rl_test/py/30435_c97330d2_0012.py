import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().rect(11,11).rect(9,9,mode='s').finalize().extrude(200)