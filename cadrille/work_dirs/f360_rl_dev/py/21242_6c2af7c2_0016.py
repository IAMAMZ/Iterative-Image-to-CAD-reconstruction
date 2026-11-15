import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,46,0))
r=w0.sketch().arc((-84,-14),(-70,-11),(-56,-11)).arc((0,-77),(87,-41)).arc((40,77),(-60,14)).segment((-69,11.5)).segment((-84,13)).arc((-100,2),(-84,-14)).assemble().push([(21,0)]).circle(27.5,mode='s').finalize().extrude(-92)