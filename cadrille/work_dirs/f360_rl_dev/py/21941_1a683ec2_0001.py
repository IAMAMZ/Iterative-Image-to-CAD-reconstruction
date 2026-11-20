import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,37,0))
r=w0.sketch().circle(100).circle(46.5,mode='s').finalize().extrude(-72)