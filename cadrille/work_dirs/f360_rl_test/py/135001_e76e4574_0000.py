import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,54))
r=w0.sketch().arc((-100,-2),(-17,-85),(71,-10)).segment((89,-10)).segment((100,-4)).segment((98,6.5)).segment((89,10)).segment((70,12)).arc((-20,85),(-100,2)).close().assemble().push([(-15,0)]).circle(68.5,mode='s').finalize().extrude(-108)