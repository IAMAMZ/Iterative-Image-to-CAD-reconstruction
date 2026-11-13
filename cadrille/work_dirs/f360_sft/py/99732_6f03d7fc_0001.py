import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().circle(29).circle(20,mode='s').finalize().extrude(-200).union(w0.sketch().circle(30).circle(20,mode='s').finalize().extrude(-20))