import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,5))
r=w0.sketch().segment((-34,-56),(-14,-57)).segment((-14,-100)).segment((22,-100)).segment((34,-22)).segment((22,-19)).arc((-13,-7),(2,31)).segment((15,60)).segment((10,95)).segment((7,100)).segment((-13,100)).segment((-34,47)).segment((-34,42)).close().assemble().push([(0,-88)]).circle(6,mode='s').finalize().extrude(-9.5)