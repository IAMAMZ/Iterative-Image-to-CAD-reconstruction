import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().circle(100).circle(94,mode='s').finalize().extrude(25).union(w0.sketch().circle(96).circle(94,mode='s').finalize().extrude(43))