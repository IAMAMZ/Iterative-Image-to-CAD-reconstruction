import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,10,0))
r=w0.sketch().segment((-30,-92),(-24,-100)).segment((30,0)).segment((-25,100)).segment((-7,0)).segment((-14,-36)).segment((-24,-82)).close().assemble().push([(2,-1)]).circle(10.5,mode='s').finalize().extrude(-20)