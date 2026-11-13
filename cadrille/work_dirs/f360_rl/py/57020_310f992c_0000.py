import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,40))
r=w0.sketch().segment((-100,-12),(100,-12)).segment((100,12)).segment((84,12)).segment((84,-3)).segment((-83,-4)).segment((-84,12)).segment((-100,12)).close().assemble().finalize().extrude(-80)