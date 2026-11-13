import cadquery as cq
w0=cq.Workplane('YZ',origin=(-67,0,0))
r=w0.workplane(offset=-33/2).cylinder(33,37).union(w0.workplane(offset=134/2).cylinder(134,46)).union(w0.sketch().circle(37).circle(16,mode='s').finalize().extrude(167))