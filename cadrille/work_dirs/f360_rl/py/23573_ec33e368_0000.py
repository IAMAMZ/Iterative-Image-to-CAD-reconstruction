import cadquery as cq
w0=cq.Workplane('YZ',origin=(-64,0,0))
r=w0.sketch().circle(100).circle(92,mode='s').finalize().extrude(50.5).union(w0.sketch().circle(100).push([(-4,0)]).circle(88,mode='s').finalize().extrude(128))