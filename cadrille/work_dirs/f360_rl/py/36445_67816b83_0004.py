import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,72))
w1=cq.Workplane('ZX',origin=(0,72,0))
r=w0.sketch().circle(100).circle(55.5,mode='s').finalize().extrude(-8).union(w1.sketch().segment((-72,-29),(-71,-29)).segment((-71,-64.5)).segment((-56,-64)).segment((-56,-29)).segment((50,-30)).segment((50,29)).segment((-56,29)).segment((-56,64.5)).segment((-71,64.5)).segment((-72,26)).close().assemble().finalize().extrude(-143))