import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,21,0))
r=w0.sketch().arc((-100,-34),(-92,-47),(-72,-47)).segment((-64,-47)).arc((-17,-64),(25,-41)).segment((100,-41)).segment((100,42)).segment((25,42)).segment((18,48)).arc((-22,64),(-70,46)).segment((-100,47)).segment((-100,32)).segment((-80,28)).arc((25,16),(-68,-33.5)).close().assemble().finalize().extrude(-41)