import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-30))
r=w0.sketch().arc((78,10),(-100,-2),(79,-7)).arc((90,-8),(100,-1)).arc((98,3),(97,7)).arc((88,7),(78,10)).assemble().push([(-11,0)]).circle(32,mode='s').finalize().extrude(60)