import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,20))
r=w0.sketch().segment((-100,64),(-84,14)).segment((-84,-55)).segment((-73,-64)).segment((-27,-67)).segment((15,-26)).segment((100,-15)).segment((99,-10)).segment((16,-20)).segment((12,-18)).segment((-22,-59)).segment((-74,-58)).segment((-78,-5)).segment((-77,27)).segment((-94,67)).close().assemble().finalize().extrude(-40)