import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
w1=cq.Workplane('XY',origin=(0,0,63))
r=w0.sketch().circle(60).circle(14.5,mode='s').finalize().extrude(-42.5).union(w0.workplane(offset=1/2).box(1.5,1.5,1.5)).union(w1.sketch().circle(100).circle(91,mode='s').finalize().extrude(-1))