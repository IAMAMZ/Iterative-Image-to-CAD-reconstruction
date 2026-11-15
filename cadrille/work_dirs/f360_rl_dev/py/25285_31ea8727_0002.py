import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().rect(13.5,8).rect(8.5,5,mode='s').finalize().extrude(200)