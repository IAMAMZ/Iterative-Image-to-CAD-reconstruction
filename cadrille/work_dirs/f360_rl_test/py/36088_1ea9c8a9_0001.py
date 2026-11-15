import cadquery as cq
w0=cq.Workplane('YZ',origin=(7,0,0))
r=w0.sketch().rect(200,150).finalize().extrude(-13.5)