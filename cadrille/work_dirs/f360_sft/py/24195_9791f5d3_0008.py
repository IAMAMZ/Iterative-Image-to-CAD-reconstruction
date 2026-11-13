import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,38))
r=w0.sketch().circle(100).circle(83,mode='s').circle(56).circle(48,mode='s').finalize().extrude(-76)