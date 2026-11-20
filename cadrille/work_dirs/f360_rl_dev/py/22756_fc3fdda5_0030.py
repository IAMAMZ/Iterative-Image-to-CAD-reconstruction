import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,4,0))
r=w0.sketch().segment((-34,-3),(-1,-8)).segment((4,-19)).segment((3,-29)).segment((4,-69.5)).segment((8,-100)).segment((20,-97)).segment((20,-8)).segment((33.5,-6.5)).segment((34.5,90)).arc((9,100),(-17,91)).segment((-18,34)).segment((-33,32)).close().assemble().push([(9,62)]).circle(9,mode='s').finalize().extrude(-7)