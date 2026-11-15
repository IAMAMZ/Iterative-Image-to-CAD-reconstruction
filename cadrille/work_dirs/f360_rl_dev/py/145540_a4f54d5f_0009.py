import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,9))
r=w0.sketch().segment((-100,-41),(-75,-41)).segment((-75,24)).segment((80,24)).segment((80,-41)).segment((100,-41)).segment((100,42)).segment((-10,42)).segment((-75.5,42)).segment((-100,42)).close().assemble().push([(0,33)]).circle(4,mode='s').finalize().extrude(-17)