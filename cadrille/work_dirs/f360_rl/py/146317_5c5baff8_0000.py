import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-2,0))
r=w0.sketch().segment((-100,-55),(-89,-63.5)).segment((89,-63.5)).segment((100,-57.5)).segment((100,53.5)).segment((89.5,63.5)).segment((-89,63)).segment((-100,55.5)).close().assemble().push([(-14.5,45)]).rect(109.5,6,mode='s').finalize().extrude(5)