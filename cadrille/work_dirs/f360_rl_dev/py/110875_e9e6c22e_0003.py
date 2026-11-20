import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,7))
r=w0.sketch().segment((-60,-38),(-59,-38)).segment((86,-8)).arc((100,9),(87,23)).segment((-50,38)).segment((-60,38)).arc((-100,1),(-60,-38)).assemble().finalize().extrude(-22).union(w0.workplane(offset=8/2).moveTo(-57,4).cylinder(8,9.5)).union(w0.workplane(offset=8/2).moveTo(85,8.5).box(1.5,1.5,8))