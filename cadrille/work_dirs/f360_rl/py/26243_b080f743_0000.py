import cadquery as cq
w0=cq.Workplane('YZ',origin=(15,0,0))
r=w0.workplane(offset=-30/2).moveTo(0,0).box(100,200,30).union(w0.workplane(offset=-2/2).box(95.5,188.5,2))