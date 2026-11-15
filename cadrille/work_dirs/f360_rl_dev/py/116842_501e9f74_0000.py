import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,13))
r=w0.sketch().segment((-100,-41),(-93,-53)).segment((66.5,-53.5)).segment((67,-36)).segment((63,-34)).segment((-65,-34)).segment((-67,34)).segment((96,32.5)).segment((100,34)).segment((100,52.5)).segment((93.5,53.5)).segment((-93,53.5)).segment((-100,41)).close().assemble().push([(0,41)]).rect(1.5,1.5).finalize().extrude(-26)