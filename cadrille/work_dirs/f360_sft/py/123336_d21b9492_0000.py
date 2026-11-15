import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,17,0))
w1=cq.Workplane('ZX',origin=(0,29,0))
r=w0.sketch().segment((-100,-18),(-42,-18)).segment((18,-30)).arc((30,-40),(45,-46)).segment((60,-51)).segment((62,-46)).arc((99,-8),(82,43)).segment((82,48)).segment((67,48)).segment((67,47)).arc((57,48),(47,47)).segment((47,48)).segment((45,48)).segment((45,47)).arc((30,42),(18,33)).segment((-35,21)).segment((-100,18)).close().assemble().finalize().extrude(-35).union(w1.sketch().arc((59,47),(76,1),(59,-45)).close().assemble().finalize().extrude(-58))