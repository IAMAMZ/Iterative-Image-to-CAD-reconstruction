import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-33))
r=w0.sketch().circle(100).circle(34.5,mode='s').finalize().extrude(35).union(w0.sketch().circle(100).circle(78,mode='s').finalize().extrude(66))