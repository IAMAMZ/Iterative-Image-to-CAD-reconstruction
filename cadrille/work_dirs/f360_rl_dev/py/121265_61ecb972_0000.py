import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-6,0))
r=w0.sketch().circle(100).circle(67.5,mode='s').push([(0.5,80.5)]).rect(7.5,11.5).finalize().extrude(-36).union(w0.sketch().circle(100).circle(66.5,mode='s').finalize().extrude(50)).union(w0.sketch().circle(98).circle(65.5,mode='s').finalize().extrude(48))