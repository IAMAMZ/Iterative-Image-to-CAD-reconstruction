import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,89))
r=w0.sketch().circle(93.5).circle(38,mode='s').finalize().extrude(-189).union(w0.sketch().circle(87).circle(38,mode='s').finalize().extrude(-131.5)).union(w0.sketch().circle(82.5).finalize().extrude(11)).union(w0.workplane(offset=11/2).cylinder(11,82))