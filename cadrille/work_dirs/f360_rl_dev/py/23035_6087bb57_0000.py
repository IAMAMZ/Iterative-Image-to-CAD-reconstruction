import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-35))
w1=cq.Workplane('YZ',origin=(90,0,0))
r=w0.workplane(offset=25/2).moveTo(40.5,84.5).box(3,31,25).union(w0.sketch().push([(-37,44.5)]).rect(4.5,111.5).finalize().extrude(26)).union(w0.sketch().push([(37,44)]).circle(21.5).finalize().extrude(50)).union(w1.sketch().segment((-100,-36),(50,-36)).segment((50,36)).segment((37,36)).segment((37,-17)).segment((-86,-17)).segment((-86,36)).segment((-100,36)).close().assemble().finalize().extrude(-180)).union(w1.workplane(offset=-6/2).moveTo(90.5,0.5).box(19.5,1.5,6))