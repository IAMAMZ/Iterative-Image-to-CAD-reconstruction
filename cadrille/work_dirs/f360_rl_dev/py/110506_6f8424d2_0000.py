import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,26))
r=w0.sketch().circle(100).circle(93.5,mode='s').finalize().extrude(-54).union(w0.workplane(offset=-13.5/2).cylinder(13.5,100)).union(w0.workplane(offset=-6/2).cylinder(6,9))