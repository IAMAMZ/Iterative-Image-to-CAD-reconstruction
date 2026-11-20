import cadquery as cq
w0=cq.Workplane('YZ',origin=(4,0,0))
w1=cq.Workplane('YZ',origin=(38,0,0))
r=w0.sketch().segment((-23,-11),(-2,-100)).segment((50,100)).segment((-18,-4)).close().assemble().finalize().extrude(-8.5).union(w1.workplane(offset=-76/2).moveTo(-43,-51).cylinder(76,6.5)).union(w1.workplane(offset=-74/2).moveTo(-43,-51).box(6.5,3.5,74))