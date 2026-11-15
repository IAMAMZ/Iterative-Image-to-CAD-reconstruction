import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,93))
r=w0.sketch().arc((-100,-2),(-6,-91),(83,-6)).segment((100,-2)).segment((100,2.5)).segment((83,6)).arc((-6,91),(-100,2)).close().assemble().push([(-9,0)]).rect(35.5,50.5,mode='s').finalize().extrude(-186.5)