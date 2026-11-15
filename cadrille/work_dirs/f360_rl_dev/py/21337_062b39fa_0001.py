import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,5,0))
r=w0.sketch().segment((-37,-97),(39,-100)).segment((39,31)).segment((38,40)).segment((38.5,79.5)).segment((38,100)).segment((-36.5,100)).segment((-37,79)).close().assemble().finalize().extrude(-9)