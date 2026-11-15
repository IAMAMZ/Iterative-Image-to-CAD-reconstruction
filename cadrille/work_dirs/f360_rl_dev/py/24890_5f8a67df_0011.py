import cadquery as cq
w0=cq.Workplane('YZ',origin=(-12,0,0))
r=w0.sketch().circle(100).circle(89,mode='s').finalize().extrude(13).union(w0.sketch().push([(0,-4)]).circle(93).circle(88,mode='s').finalize().extrude(23))