import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,0))
r=w0.sketch().circle(100).circle(44,mode='s').finalize().extrude(-23).union(w0.sketch().circle(100).circle(44,mode='s').finalize().extrude(22)).union(w0.sketch().circle(99).circle(44,mode='s').finalize().extrude(23))