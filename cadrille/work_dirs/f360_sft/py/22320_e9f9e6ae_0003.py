import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,27,0))
r=w0.sketch().segment((-100,-27),(-28,-99)).segment((-21,-92)).segment((-20,-99)).segment((73,-74)).segment((71,-64)).segment((100,27)).segment((28,99)).segment((21,92)).segment((20,99)).segment((-73,74)).segment((-71,64)).segment((-100,-20)).segment((-97,-21)).close().assemble().circle(45,mode='s').finalize().extrude(-54)