import cadquery as cq
w0=cq.Workplane('YZ',origin=(-20,0,0))
r=w0.sketch().circle(100).circle(35.5,mode='s').finalize().extrude(12).union(w0.sketch().circle(46).circle(35.5,mode='s').finalize().extrude(39))