import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,4))
r=w0.sketch().rect(200,113).finalize().extrude(-8)