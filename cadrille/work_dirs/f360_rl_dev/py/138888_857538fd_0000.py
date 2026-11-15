import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-92))
w1=cq.Workplane('XY',origin=(0,0,-100))
r=w0.workplane(offset=192/2).cylinder(192,10).union(w1.sketch().circle(18).circle(7.5,mode='s').finalize().extrude(7.5)).union(w1.workplane(offset=2/2).box(1.5,1.5,1.5))