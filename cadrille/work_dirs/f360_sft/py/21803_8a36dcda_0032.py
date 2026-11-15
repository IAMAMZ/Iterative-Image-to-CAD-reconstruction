import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-100,0))
r=w0.sketch().segment((-67,-46),(-57,-46)).arc((0,-74),(57,-46)).segment((67,-46)).segment((67,-30)).arc((74,0),(67,30)).segment((67,46)).segment((57,46)).arc((0,74),(-57,46)).segment((-67,46)).segment((-67,30)).arc((-74,0),(-67,-30)).close().assemble().finalize().extrude(11).union(w0.workplane(offset=200/2).cylinder(200,100))