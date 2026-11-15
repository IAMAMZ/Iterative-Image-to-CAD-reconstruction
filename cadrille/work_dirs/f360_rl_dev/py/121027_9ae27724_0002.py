import cadquery as cq
w0=cq.Workplane('YZ',origin=(19,0,0))
r=w0.sketch().segment((-100,-21),(-72,-47)).segment((72,-47)).segment((100,-20)).segment((100,47)).segment((62.5,47)).segment((62,-4)).segment((54,-12)).segment((-57,-12)).segment((-69,-3)).segment((-61,8.5)).segment((-60,47)).segment((-84,46)).segment((-100,20)).close().assemble().finalize().extrude(-37.5)