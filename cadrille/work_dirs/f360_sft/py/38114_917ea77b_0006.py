import cadquery as cq
w0=cq.Workplane('YZ',origin=(-75,0,0))
r=w0.sketch().circle(100).circle(90,mode='s').finalize().extrude(150)