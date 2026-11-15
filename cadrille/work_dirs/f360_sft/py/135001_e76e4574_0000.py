import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,54))
r=w0.sketch().arc((70,10),(-100,-2),(71,-10)).arc((86,-11),(98,-4)).segment((100,-4)).segment((100,4)).segment((98,4)).arc((86,12),(70,10)).assemble().push([(-15,0)]).circle(68,mode='s').finalize().extrude(-108)