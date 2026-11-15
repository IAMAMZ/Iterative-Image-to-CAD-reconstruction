import cadquery as cq
w0=cq.Workplane('YZ',origin=(13,0,0))
r=w0.sketch().segment((-100,-62),(79,-62.5)).arc((89,-57),(100,-43)).segment((100,46.5)).arc((89,58),(79,62.5)).segment((-100,63)).close().assemble().finalize().extrude(-25)