import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,6))
r=w0.sketch().circle(36).circle(34.5,mode='s').finalize().extrude(-106).union(w0.sketch().circle(40).circle(34.5,mode='s').finalize().extrude(94))