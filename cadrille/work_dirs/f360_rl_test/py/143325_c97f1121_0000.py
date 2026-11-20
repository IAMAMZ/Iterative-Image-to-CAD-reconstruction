import cadquery as cq
w0=cq.Workplane('YZ',origin=(-64,0,0))
r=w0.sketch().circle(97).circle(91.5,mode='s').finalize().extrude(54.5).union(w0.sketch().circle(100).push([(0,-4)]).circle(88,mode='s').finalize().extrude(128))