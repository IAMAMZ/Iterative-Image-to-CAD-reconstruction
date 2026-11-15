import cadquery as cq
w0=cq.Workplane('YZ',origin=(-54,0,0))
r=w0.sketch().circle(100).circle(71.5,mode='s').finalize().extrude(18).union(w0.sketch().circle(79).circle(70.5,mode='s').finalize().extrude(77.5)).union(w0.sketch().circle(73.5).circle(55,mode='s').finalize().extrude(107))