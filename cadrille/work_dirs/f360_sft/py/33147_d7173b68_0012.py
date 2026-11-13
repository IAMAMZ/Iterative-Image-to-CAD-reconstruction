import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-31))
r=w0.sketch().arc((83,10),(-100,-2),(84,-6)).arc((92,-6),(100,-2)).arc((98,3),(97,8)).arc((90,7),(83,10)).assemble().finalize().extrude(62)