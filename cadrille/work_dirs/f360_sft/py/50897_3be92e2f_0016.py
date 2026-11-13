import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,6,0))
r=w0.sketch().segment((-100,2),(-14,2)).segment((-87,-52)).segment((-53,-88)).segment((10,-25)).segment((1,-100)).segment((49,-88)).segment((10,2)).segment((87,-49)).segment((100,-2)).segment((14,24)).segment((-10,-2)).segment((-10,100)).segment((-49,88)).segment((-10,-2)).segment((-87,49)).close().assemble().finalize().extrude(-13)