import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,93))
r=w0.sketch().rect(200,8).rect(6,8,mode='s').finalize().extrude(-186)