import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((98,-2),(98,2)).segment((99,2)).arc((-99,14),(98,-2)).assemble().push([(-1,0)]).rect(40,38,mode='s').finalize().extrude(12)