import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,5))
r=w0.sketch().rect(200,114).finalize().extrude(-8.5)