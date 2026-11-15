import cadquery as cq
w0=cq.Workplane('YZ',origin=(84,0,0))
r=w0.sketch().circle(7.5).circle(3,mode='s').finalize().extrude(-184).union(w0.workplane(offset=16/2).cylinder(16,3)).union(w0.workplane(offset=16/2).box(3,1.5,16))