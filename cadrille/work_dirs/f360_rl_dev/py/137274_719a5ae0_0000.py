import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,38))
w1=cq.Workplane('XY',origin=(0,0,-36))
r=w0.workplane(offset=-112/2).moveTo(0,0).box(176.5,36.5,112).union(w0.sketch().segment((-90,-100),(90,-100)).segment((90,20)).segment((-10,99.5)).segment((-27.5,100)).segment((-90,100)).close().assemble().finalize().extrude(37)).union(w1.sketch().segment((-90,-100),(90,-100)).segment((90,16)).segment((-7,100)).segment((-27.5,100)).segment((-90,100)).close().assemble().push([(-20,58)]).circle(20,mode='s').finalize().extrude(-39))