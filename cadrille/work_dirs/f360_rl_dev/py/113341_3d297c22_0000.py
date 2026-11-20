import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
w1=cq.Workplane('XY',origin=(0,0,-93))
r=w0.workplane(offset=8/2).moveTo(-41,-18).cylinder(8,38).union(w0.workplane(offset=200/2).moveTo(72,48).cylinder(200,8)).union(w1.workplane(offset=6/2).moveTo(-41,-48.5).box(1.5,13.5,1.5))