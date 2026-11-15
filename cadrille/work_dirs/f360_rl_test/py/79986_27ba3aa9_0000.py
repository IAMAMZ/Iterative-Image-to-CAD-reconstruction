import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,68))
r=w0.workplane(offset=-135/2).cylinder(135,100).union(w0.workplane(offset=-69/2).cylinder(69,91))