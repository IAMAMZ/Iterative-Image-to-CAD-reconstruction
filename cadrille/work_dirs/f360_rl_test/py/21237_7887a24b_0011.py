import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-87))
r=w0.sketch().arc((14,-17),(21,0),(14,17)).segment((14,9.5)).close().assemble().finalize().extrude(-13).union(w0.sketch().push([(-0,0)]).circle(20.5).circle(17.5,mode='s').finalize().extrude(187))