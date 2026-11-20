import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-59,0))
w1=cq.Workplane('XY',origin=(0,0,15))
r=w0.sketch().segment((-16,-8),(0,-18)).segment((16,-8)).segment((16,8.5)).segment((0,18)).segment((-14,8.5)).segment((-16,7)).close().assemble().finalize().extrude(159).union(w1.sketch().push([(0,-72)]).circle(27.5).push([(0,-79)]).circle(8.5,mode='s').finalize().extrude(-30)).union(w1.workplane(offset=-11/2).moveTo(0.5,97.5).box(1.5,1,1.5))