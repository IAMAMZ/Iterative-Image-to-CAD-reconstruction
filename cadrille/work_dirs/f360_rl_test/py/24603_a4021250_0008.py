import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,9))
r=w0.sketch().segment((-100,-46),(-26,-46)).segment((-26,-92)).segment((100,-91.5)).segment((100,91.5)).segment((-26.5,91.5)).segment((-28,89)).segment((-100,-35)).close().assemble().push([(44,32)]).circle(28.5,mode='s').finalize().extrude(-17.5)