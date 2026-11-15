import cadquery as cq
w0=cq.Workplane('YZ',origin=(38,0,0))
r=w0.sketch().segment((-37,-100),(-29,-100)).arc((25,-56),(38,-2)).segment((38,100)).segment((25,100)).segment((25,-3)).arc((21,-54),(-23,-87)).segment((-33,-92)).segment((-37,-94)).close().assemble().finalize().extrude(-76)