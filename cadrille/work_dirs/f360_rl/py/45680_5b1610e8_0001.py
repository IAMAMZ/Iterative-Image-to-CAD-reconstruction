import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().rect(4,4).rect(3,3,mode='s').finalize().extrude(200)