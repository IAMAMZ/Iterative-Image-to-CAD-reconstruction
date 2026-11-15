import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,7))
r=w0.sketch().circle(36).circle(34,mode='s').finalize().extrude(-107).union(w0.sketch().circle(40).circle(34,mode='s').finalize().extrude(93))