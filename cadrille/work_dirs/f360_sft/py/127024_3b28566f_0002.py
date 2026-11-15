import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-29))
r=w0.sketch().segment((-100,4),(-98,-7)).segment((98,-7)).segment((98,-4)).segment((100,-4)).segment((98,7)).segment((-98,7)).segment((-98,4)).close().assemble().finalize().extrude(58)