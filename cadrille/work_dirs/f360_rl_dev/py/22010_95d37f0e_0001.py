import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,39))
w1=cq.Workplane('ZX',origin=(0,-100,0))
r=w0.sketch().push([(0,81)]).circle(19.5).circle(9,mode='s').finalize().extrude(-56.5).union(w0.sketch().segment((-72,-100),(72,-77.5)).segment((10,67)).segment((-10,51)).close().assemble().push([(0,-5.5)]).rect(70.5,119.5,mode='s').finalize().extrude(-5)).union(w1.sketch().push([(-11,0)]).rect(100,143.5).push([(-11,47)]).circle(6,mode='s').finalize().extrude(9)).union(w1.workplane(offset=1/2).moveTo(57,6.5).box(1.5,1,1))