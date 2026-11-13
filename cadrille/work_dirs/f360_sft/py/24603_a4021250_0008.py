import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-100,-47),(-27,-47)).segment((-27,-92)).segment((100,-92)).segment((100,92)).segment((-27,92)).segment((-27,91)).segment((-100,-36)).close().assemble().push([(44,33)]).circle(28,mode='s').finalize().extrude(17)