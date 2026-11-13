import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,14))
w1=cq.Workplane('XY',origin=(0,0,47))
r=w0.sketch().circle(100).circle(83,mode='s').finalize().extrude(-28).union(w1.sketch().circle(21).circle(10,mode='s').finalize().extrude(-95))