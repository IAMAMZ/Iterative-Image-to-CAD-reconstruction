import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,21))
r=w0.sketch().arc((62,11),(-100,-2),(63,-11)).segment((71,-11)).arc((85,-13),(97,-7)).segment((100,-7)).segment((100,1)).segment((97,1)).arc((87,11),(71,9)).segment((62,9)).close().assemble().push([(-18,0)]).circle(18,mode='s').finalize().extrude(-42)