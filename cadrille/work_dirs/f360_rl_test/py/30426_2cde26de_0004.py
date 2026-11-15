import cadquery as cq
w0=cq.Workplane('YZ',origin=(68,0,0))
r=w0.workplane(offset=-168/2).cylinder(168,36.5).union(w0.sketch().circle(46).finalize().extrude(-136)).union(w0.sketch().circle(37).circle(16,mode='s').finalize().extrude(32))