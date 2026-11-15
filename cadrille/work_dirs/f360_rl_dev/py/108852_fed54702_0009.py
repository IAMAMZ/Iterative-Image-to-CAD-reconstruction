import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().segment((-14,-83),(13,-83)).segment((13,-6.5)).segment((-1,-6)).segment((-1,12)).segment((13.5,12)).segment((13.5,83)).segment((-14,83)).close().assemble().finalize().extrude(-200)