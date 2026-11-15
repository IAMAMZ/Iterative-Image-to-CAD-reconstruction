import cadquery as cq
w0=cq.Workplane('YZ',origin=(16,0,0))
r=w0.workplane(offset=-32/2).cylinder(32,100)