import cadquery as cq
w0=cq.Workplane('YZ',origin=(-3,0,0))
r=w0.sketch().segment((-42,-100),(42,-100)).segment((42,-36)).segment((13,-36)).segment((13,77)).segment((29,77)).segment((29,100)).segment((-7,100)).segment((-42,67)).segment((-42,56)).segment((-40,56)).segment((-40,53)).segment((-42,53)).close().assemble().push([(-11,13)]).circle(11,mode='s').finalize().extrude(6)