import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-1,0))
r=w0.sketch().segment((-82,22),(-62,6)).segment((-62,-100)).segment((62,-100)).segment((62,8)).segment((82,26)).segment((62,57)).segment((62,67)).segment((55,89)).segment((49,100)).segment((-49,100)).segment((-62,80)).segment((-50,63)).segment((-69,47)).close().assemble().push([(-0,40)]).circle(20.5,mode='s').finalize().extrude(2)