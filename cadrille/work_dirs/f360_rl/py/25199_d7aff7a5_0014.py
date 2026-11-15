import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,20,0))
r=w0.sketch().arc((-100,42),(-89,5),(-25,-39)).segment((75,-59)).segment((77,-48)).segment((-16,-34)).segment((-88,15)).segment((-87,33)).segment((88,30)).segment((100,32.5)).segment((100,59)).segment((89,59)).segment((87,42)).close().assemble().finalize().extrude(-39)