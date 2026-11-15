import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,4))
r=w0.sketch().rect(200,90).finalize().extrude(-6.5)