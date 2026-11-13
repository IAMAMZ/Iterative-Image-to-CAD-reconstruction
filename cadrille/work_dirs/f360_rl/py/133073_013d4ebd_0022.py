import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,5,0))
r=w0.sketch().circle(100).finalize().extrude(-10)