import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,20))
r=w0.sketch().circle(100).finalize().extrude(-40)