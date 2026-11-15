import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,98))
r=w0.workplane(offset=-196/2).moveTo(0,29.5).box(200,19,196).union(w0.sketch().push([(0,29)]).rect(10.5,17.5).finalize().extrude(-10.5)).union(w0.workplane(offset=-20/2).moveTo(0,-10).cylinder(20,30)).union(w0.workplane(offset=-10/2).moveTo(97,36.5).box(2.5,1.5,1))