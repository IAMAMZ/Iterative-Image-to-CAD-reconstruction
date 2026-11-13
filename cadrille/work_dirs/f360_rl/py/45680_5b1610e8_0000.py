import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().rect(8.5,8.5).rect(7,6.5,mode='s').finalize().extrude(200)