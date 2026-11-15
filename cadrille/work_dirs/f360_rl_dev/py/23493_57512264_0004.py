import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,25))
r=w0.sketch().segment((-100,-7),(96,-7.5)).segment((100,-1)).segment((71,7)).segment((-70,7)).segment((-100,7)).close().assemble().finalize().extrude(-48)