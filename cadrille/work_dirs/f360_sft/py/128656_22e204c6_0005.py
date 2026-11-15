import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,17))
r=w0.sketch().arc((86,10),(-100,-2),(87,-4)).arc((93,-4),(100,0)).arc((98,4),(96,8)).arc((91,7),(86,10)).assemble().push([(-6,0)]).circle(2,mode='s').finalize().extrude(-34)