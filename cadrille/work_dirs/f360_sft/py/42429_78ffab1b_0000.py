import cadquery as cq
w0=cq.Workplane('YZ',origin=(-69,0,0))
r=w0.workplane(offset=-31/2).cylinder(31,31).union(w0.workplane(offset=169/2).cylinder(169,8))