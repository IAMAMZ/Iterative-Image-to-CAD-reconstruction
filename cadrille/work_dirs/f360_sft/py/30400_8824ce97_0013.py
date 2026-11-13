import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-44,0))
r=w0.sketch().circle(100).circle(46,mode='s').finalize().extrude(64).union(w0.sketch().circle(57).circle(44,mode='s').finalize().extrude(88))