import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,11))
r=w0.sketch().segment((-74,-6),(-51,-6.5)).segment((-22,-35)).segment((-22.5,-100)).segment((60,-100)).segment((74.5,-86)).segment((74,-34)).segment((4,79)).segment((5,100)).segment((-74.5,100)).close().assemble().finalize().extrude(-20.5)