import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
w1=cq.Workplane('YZ',origin=(47,0,0))
r=w0.sketch().push([(4,0)]).circle(12.5).circle(8.5,mode='s').finalize().extrude(3.5).union(w0.workplane(offset=183/2).moveTo(4,9.5).cylinder(183,2)).union(w1.sketch().push([(0,95)]).rect(28.5,10).rect(9.5,8).finalize().extrude(-94)).union(w1.workplane(offset=-92/2).moveTo(-9.5,95.5).box(2.5,3,1))