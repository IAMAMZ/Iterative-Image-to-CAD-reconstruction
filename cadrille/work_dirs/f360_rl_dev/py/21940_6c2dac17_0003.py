import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,6))
r=w0.sketch().segment((-86,-19),(-23,-19)).segment((-19,-22)).segment((80,-22)).arc((100,0),(80,21.5)).segment((59.5,22)).segment((-70,22)).segment((-86,21)).arc((-100,3),(-86,-18)).close().assemble().finalize().extrude(-10.5)