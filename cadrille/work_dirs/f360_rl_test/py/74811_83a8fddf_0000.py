import cadquery as cq
w0=cq.Workplane('YZ',origin=(16.5,0,0))
r=w0.sketch().circle(100).finalize().extrude(-32)