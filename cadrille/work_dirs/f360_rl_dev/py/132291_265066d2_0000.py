import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,32))
w1=cq.Workplane('YZ',origin=(-32,0,0))
r=w0.sketch().segment((-31,-100),(32,-100)).segment((32,-72)).segment((-2,-18.5)).segment((-2,29)).segment((-32.5,10)).close().assemble().finalize().extrude(-12).union(w1.sketch().segment((-100,-32),(100,-32)).segment((100,32.5)).segment((-10,32)).segment((-69,-17.5)).segment((-100,-17)).close().assemble().push([(-87,-29)]).rect(4.5,4).push([(72,0)]).circle(16.5,mode='s').finalize().extrude(8)).union(w1.workplane(offset=63.5/2).moveTo(-87,-26.5).box(25,9.5,63.5))