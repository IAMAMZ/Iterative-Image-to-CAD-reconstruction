import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,50))
w1=cq.Workplane('XY',origin=(0,0,-50))
r=w0.sketch().circle(98.5).circle(74,mode='s').finalize().extrude(-16).union(w1.sketch().circle(100).circle(75,mode='s').finalize().extrude(18.5))