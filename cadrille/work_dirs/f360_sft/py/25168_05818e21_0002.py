import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-88))
r=w0.sketch().arc((81,10),(-100,-2),(82,-6)).arc((90,-7),(98,-3)).segment((100,-3)).segment((100,3)).segment((98,3)).arc((90,7),(81,10)).assemble().finalize().extrude(176)