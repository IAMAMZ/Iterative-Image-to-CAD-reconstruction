import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,10))
w1=cq.Workplane('YZ',origin=(49,0,0))
r=w0.sketch().segment((-79,-20),(50,-20)).segment((50,0)).segment((-64,0)).arc((-95,13),(-93,-17)).close().assemble().push([(-80,0)]).circle(14.5,mode='s').finalize().extrude(-20).union(w1.sketch().segment((-18,-5),(-9,-7)).segment((-4,-5)).segment((-4,4.5)).segment((-9,6.5)).segment((-13,5.5)).segment((-16,0)).segment((-18,0)).close().assemble().finalize().extrude(51))