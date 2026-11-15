import cadquery as cq
w0=cq.Workplane('YZ',origin=(8,0,0))
r=w0.sketch().segment((-39,99),(3,79)).segment((4.5,81)).segment((-39,100)).close().assemble().reset().face(w0.sketch().segment((-2,-77),(39,-100)).segment((39,-99)).segment((0,-76)).segment((3.5,-76)).segment((2.5,77.5)).segment((0,76.5)).close().assemble()).finalize().extrude(-16)