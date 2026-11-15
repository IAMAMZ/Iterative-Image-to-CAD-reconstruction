import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,3))
r=w0.sketch().rect(200,122).finalize().extrude(-6.5)