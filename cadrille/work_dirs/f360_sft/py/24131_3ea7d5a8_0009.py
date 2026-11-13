import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-23))
w1=cq.Workplane('ZX',origin=(0,21,0))
r=w0.sketch().rect(84,42).push([(-22,0)]).circle(6,mode='s').push([(22,0)]).circle(6,mode='s').finalize().extrude(123).union(w1.sketch().arc((-16,41),(-99,-10),(-4,-27)).arc((1,-24),(5,-20)).segment((100,-20)).segment((100,41)).close().assemble().push([(-49,0)]).circle(42,mode='s').finalize().extrude(-42))