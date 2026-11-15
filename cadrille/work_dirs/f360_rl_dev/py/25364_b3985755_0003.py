import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,9))
r=w0.sketch().segment((-100,19),(65,-24)).segment((100,-24)).segment((100,-19.5)).segment((64,-19)).segment((60,-17)).segment((-97,24)).segment((-100,23.5)).close().assemble().finalize().extrude(-18)