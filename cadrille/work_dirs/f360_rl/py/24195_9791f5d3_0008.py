import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,38))
r=w0.sketch().circle(100).circle(52.5,mode='s').circle(63).circle(48.5,mode='s').finalize().extrude(-74.5)