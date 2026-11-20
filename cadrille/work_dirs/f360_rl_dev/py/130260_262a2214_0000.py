import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,47))
w1=cq.Workplane('XY',origin=(0,0,30))
r=w0.workplane(offset=5/2).moveTo(0,50.5).box(1.5,21.5,5).union(w0.workplane(offset=53/2).moveTo(0,46).cylinder(53,14)).union(w1.workplane(offset=-130/2).moveTo(4.5,-61).box(2.5,1.5,130)).union(w1.workplane(offset=-130/2).moveTo(4.5,-61).box(1,1,1))