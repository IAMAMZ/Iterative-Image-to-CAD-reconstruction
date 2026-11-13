import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,79))
w1=cq.Workplane('XY',origin=(0,0,-79))
r=w0.sketch().circle(25.5).circle(20,mode='s').finalize().extrude(-170.5).union(w0.sketch().circle(30).circle(20,mode='s').finalize().extrude(21)).union(w1.sketch().circle(30).circle(20,mode='s').finalize().extrude(-21))