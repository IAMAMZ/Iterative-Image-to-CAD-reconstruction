import cadquery as cq
w0=cq.Workplane('YZ',origin=(31,0,0))
w1=cq.Workplane('XY',origin=(0,0,31))
r=w0.sketch().segment((-100,-19),(-86,-14.5)).segment((-86,19)).segment((-100,17)).close().assemble().finalize().extrude(-62.5).union(w1.sketch().push([(0,7)]).rect(62.5,186.5).push([(0,74)]).circle(12,mode='s').finalize().extrude(-62.5)).union(w1.workplane(offset=-8/2).moveTo(0.5,97.5).box(1.5,5,1.5))