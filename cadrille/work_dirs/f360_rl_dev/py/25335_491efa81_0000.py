import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,72))
r=w0.sketch().circle(100).circle(94.5,mode='s').push([(-32,-77)]).circle(6).push([(0,-86)]).circle(9.5).finalize().extrude(-144)