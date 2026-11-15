import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,63,0))
w1=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().arc((-62,-20),(-58,-43),(-37,-55)).arc((25,-58),(100,-90)).segment((100,-57.5)).arc((33,-36),(-31,-26)).segment((-32,47.5)).segment((-38,89)).segment((-70,78.5)).segment((-60,-17)).close().assemble().finalize().extrude(-126).union(w1.workplane(offset=50/2).moveTo(19.5,0).box(53.5,18.5,50))