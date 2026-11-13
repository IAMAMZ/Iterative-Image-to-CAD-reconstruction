import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,17,0))
w1=cq.Workplane('ZX',origin=(0,30,0))
r=w0.sketch().segment((-100,-18),(-42,-18)).segment((10,-25)).segment((53,-48)).segment((89,-11.5)).segment((59,48)).segment((10,30)).segment((-20,23)).segment((-50,17)).segment((-100,17)).close().assemble().finalize().extrude(-34.5).union(w1.sketch().arc((58,-50),(96,-20),(87,32)).segment((82.5,50)).segment((58.5,48)).segment((80,19)).close().assemble().finalize().extrude(-58.5)).union(w1.workplane(offset=-19/2).moveTo(77.5,0.5).box(1.5,1.5,1))