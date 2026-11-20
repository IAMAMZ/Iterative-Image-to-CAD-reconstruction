import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,7))
r=w0.sketch().segment((-48,-100),(48,-100)).segment((47,54.5)).segment((48,100)).segment((-48,100)).close().assemble().push([(22,90)]).rect(27.5,9,mode='s').finalize().extrude(-12)