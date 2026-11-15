import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,4))
r=w0.sketch().arc((-90,-13),(4,-89),(89,-10)).segment((100,-7.5)).segment((100,7)).segment((90,13)).arc((4,89),(-90,10)).arc((-100,0),(-90,-13)).assemble().push([(0,0)]).circle(44,mode='s').finalize().extrude(-7)