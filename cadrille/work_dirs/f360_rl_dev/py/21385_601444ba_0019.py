import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,33.5,0))
w1=cq.Workplane('XY',origin=(0,0,14))
r=w0.sketch().arc((-36,7),(-30,-17),(-2,-27)).segment((16,-44)).segment((15,-100)).segment((36.5,-100)).segment((36.5,100)).segment((15,100)).segment((15,33)).segment((-6,33)).segment((-20,25)).segment((-32,14)).close().assemble().push([(-9,-0)]).circle(12,mode='s').finalize().extrude(-66.5).union(w1.workplane(offset=21/2).moveTo(97.5,0.5).box(1,1.5,21)).union(w1.workplane(offset=-10/2).moveTo(97.5,0.5).box(1.5,1.5,1))