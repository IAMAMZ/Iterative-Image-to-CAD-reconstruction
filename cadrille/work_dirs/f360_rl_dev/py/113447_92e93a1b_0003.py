import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,2))
r=w0.sketch().segment((-100,-35),(100,-35)).segment((90,35)).segment((-100,35)).segment((-100,31)).segment((-96,19)).segment((-100,16)).close().assemble().push([(-1.5,0)]).rect(157.5,29,mode='s').finalize().extrude(-4.5)