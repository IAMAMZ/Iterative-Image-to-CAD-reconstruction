import cadquery as cq
w0=cq.Workplane('YZ',origin=(50,0,0))
w1=cq.Workplane('XY',origin=(0,0,75))
r=w0.sketch().segment((-75,-75),(75,-75)).segment((75,24)).segment((-75,-26)).close().assemble().finalize().extrude(-150).union(w1.sketch().segment((-100,-75),(50,-75)).segment((49,25)).segment((100,25)).segment((100,75)).segment((-10,75)).segment((-100,75)).close().assemble().push([(-52,25)]).circle(24.5,mode='s').finalize().extrude(-150)).union(w1.workplane(offset=-69/2).moveTo(97,61.5).box(2.5,1.5,6))