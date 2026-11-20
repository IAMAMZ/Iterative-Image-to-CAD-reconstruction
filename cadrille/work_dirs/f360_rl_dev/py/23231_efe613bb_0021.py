import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,43,0))
r=w0.sketch().circle(70).circle(53.5,mode='s').finalize().extrude(-87).union(w0.sketch().circle(100).circle(54.5,mode='s').finalize().extrude(-17.5))