import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,5,0))
r=w0.sketch().segment((-100,67),(69,67)).segment((68,-100)).segment((100,-100)).segment((100,100)).segment((-6,100)).segment((-100,100)).close().assemble().push([(-40.5,83)]).rect(5.5,4).push([(84,-40)]).rect(4.5,6).push([(84,83)]).rect(4.5,4).finalize().extrude(-9)