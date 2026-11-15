import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,7,0))
r=w0.sketch().segment((-59,-100),(59,-100)).segment((58,-95)).segment((58,95)).segment((58,100)).segment((-58.5,100)).segment((-58,95)).close().assemble().push([(0,0)]).rect(105,188.5,mode='s').finalize().extrude(-12)