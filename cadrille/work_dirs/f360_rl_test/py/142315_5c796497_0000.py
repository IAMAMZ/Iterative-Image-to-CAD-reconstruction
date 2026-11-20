import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,7))
r=w0.sketch().rect(200,139).finalize().extrude(-13.5)