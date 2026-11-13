import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,14))
r=w0.sketch().segment((-31,-98),(-19,-100)).segment((31,-98)).segment((31,98)).segment((19,100)).segment((-19,99)).segment((-31,98)).close().assemble().push([(0,-58)]).circle(12,mode='s').push([(0,58)]).circle(12,mode='s').finalize().extrude(-27)