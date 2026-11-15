import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,7))
r=w0.sketch().push([(-75,0)]).circle(25).circle(16.5,mode='s').reset().face(w0.sketch().segment((-59,-13),(53,-13)).arc((100,0),(53,13)).segment((-50,13)).segment((-59,13)).close().assemble()).push([(-57,19)]).rect(1.5,1).push([(75,0)]).circle(16.5,mode='s').finalize().extrude(-12.5)