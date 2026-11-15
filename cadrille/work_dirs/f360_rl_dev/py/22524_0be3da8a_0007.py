import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,40))
r=w0.sketch().circle(100).circle(60,mode='s').finalize().extrude(-80)