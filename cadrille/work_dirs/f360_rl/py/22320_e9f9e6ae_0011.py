import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-2))
r=w0.sketch().segment((-100,6),(-64,-2)).segment((-67,-13)).segment((-56,-22)).segment((-45,3)).segment((100,4)).segment((100,11.5)).segment((-44,22)).segment((-67,19)).segment((-100,11)).close().assemble().finalize().extrude(5.5)