import cadquery as cq
w0=cq.Workplane('YZ',origin=(8,0,0))
r=w0.sketch().segment((-82,100),(-62,7)).segment((-74,-4)).segment((-58,-83)).segment((-39,-100)).segment((82.5,-100)).segment((-49,97)).segment((-60,100)).close().assemble().push([(-25,-43)]).circle(11,mode='s').finalize().extrude(-14.5)