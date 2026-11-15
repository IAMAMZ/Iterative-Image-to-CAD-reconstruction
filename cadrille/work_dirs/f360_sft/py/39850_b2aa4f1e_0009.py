import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-100,-40),(58,-40)).arc((72,-35),(80,-23)).segment((80,37)).segment((100,37)).segment((100,40)).segment((20,40)).segment((20,-30)).segment((-100,-30)).close().assemble().finalize().extrude(40)