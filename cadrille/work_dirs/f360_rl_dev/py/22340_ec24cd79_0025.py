import cadquery as cq
w0=cq.Workplane('YZ',origin=(35,0,0))
r=w0.sketch().circle(100).circle(31.5,mode='s').finalize().extrude(-68.5)