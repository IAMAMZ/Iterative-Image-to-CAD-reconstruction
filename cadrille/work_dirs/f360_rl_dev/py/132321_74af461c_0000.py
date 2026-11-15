import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,22,0))
r=w0.sketch().segment((-71,-36),(23,-93)).arc((63,-97),(91,-62.5)).segment((92.5,58)).arc((63,97),(16,85)).segment((-1,77)).segment((-32,63)).segment((-69,41)).arc((-93,5),(-79,-27)).close().assemble().push([(-50,0)]).circle(22,mode='s').push([(45,-57)]).circle(22,mode='s').push([(50,56)]).circle(22.5,mode='s').finalize().extrude(-44.5)