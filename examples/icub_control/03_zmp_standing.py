#!/xde

import xde_world_manager as xwm
import xde_robot_loader  as xrl
import xde_resources     as xr
import physicshelper
import lgsm
import time

pi = lgsm.np.pi



##### AGENTS
dt = 0.01
wm = xwm.WorldManager()
wm.createAllAgents(dt, lmd_max=.2)
wm.resizeWindow("mainWindow",  640, 480, 1000, 50)


##### GROUND
groundWorld = xrl.createWorldFromUrdfFile(xr.ground, "ground", [0,0,0,1,0,0,0], True, 0.001, 0.001)
wm.addWorld(groundWorld)


##### ROBOT
rname = "robot"
fixed_base = False
robotWorld = xrl.createWorldFromUrdfFile(xr.icub_simple, rname, [0,0,0.6,1,0,0,0], fixed_base, .001, 0.001)
wm.addWorld(robotWorld)
robot = wm.phy.s.GVM.Robot(rname)
robot.enableGravity(True)
N  = robot.getJointSpaceDim()
dynModel = physicshelper.createDynamicModel(robotWorld, rname)


##### SET INTERACTION
wm.ms.setContactLawForMaterialPair("material.metal", "material.concrete", 1, 1.5)
robot.enableContactWithBody("ground.ground", True)
wm.addInteraction([(rname+"."+b,"ground.ground") for b in ["l_foot", "r_foot"]]) # to display contact


##### SET INITIAL STATE
qinit = lgsm.zeros(N)
# correspond to:    l_elbow_pitch     r_elbow_pitch     l_knee             r_knee             l_ankle_pitch      r_ankle_pitch      l_shoulder_roll          r_shoulder_roll
for name, val in [("l_arm", pi/8.), ("r_arm", pi/8.), ("l_thigh", -0.05), ("r_thigh", -0.05), ("l_shank", -0.05), ("r_shank", -0.05), ("l_shoulder_1", pi/8.), ("r_shoulder_1", pi/8.)]:
    qinit[robot.getSegmentIndex(rname+"."+name)] = val

robot.setJointPositions(qinit)
dynModel.setJointPositions(qinit)
robot.setJointVelocities(lgsm.zeros(N))
dynModel.setJointVelocities(lgsm.zeros(N))


##### CTRL
import xde_isir_controller as xic
#dynModel = physicshelper.createDynamicModel(robotWorld, rname)
ctrl = xic.ISIRCtrl("/home/joe/dev/EReval/orcisir_ISIRController/build/src", dynModel, rname, wm.phy, wm.icsync, "quadprog", True)


##### SET TASKS
# this ...
#N0 = 6 if fixed_base is False else 0
#partialTask = ctrl.createPartialTask("partial", range(N0, N+N0), 0.0001, kp=9., pos_des=qinit)
# ... is equivalent to that:
fullTask = ctrl.createFullTask("full", 0.0001, kp=9., pos_des=qinit)

waistTask   = ctrl.createFrameTask("waist", rname+'.waist', lgsm.Displacement(), "RZ", 1., kp=36., pos_des=lgsm.Displacement(0,0,.58))

back_name   = [rname+"."+n for n in ['lap_belt_1', 'lap_belt_2', 'chest']]
backTask    = ctrl.createPartialTask("back", back_name, 0.001, kp=16., pos_des=lgsm.zeros(3))


sqrt2on2 = lgsm.np.sqrt(2.)/2.
RotLZdown = lgsm.Quaternion(-sqrt2on2,0.0,-sqrt2on2,0.0) * lgsm.Quaternion(0.0,1.0,0.0,0.0)
RotRZdown = lgsm.Quaternion(0.0, sqrt2on2,0.0, sqrt2on2) * lgsm.Quaternion(0.0,1.0,0.0,0.0)

ctrl.createContactTask("CLF0", rname+".l_foot", lgsm.Displacement(lgsm.vector(-.039,-.027,-.031), RotLZdown), 1.5, 0.) # mu, margin
ctrl.createContactTask("CLF1", rname+".l_foot", lgsm.Displacement(lgsm.vector(-.039, .027,-.031), RotLZdown), 1.5, 0.) # mu, margin
ctrl.createContactTask("CLF2", rname+".l_foot", lgsm.Displacement(lgsm.vector(-.039, .027, .099), RotLZdown), 1.5, 0.) # mu, margin
ctrl.createContactTask("CLF3", rname+".l_foot", lgsm.Displacement(lgsm.vector(-.039,-.027, .099), RotLZdown), 1.5, 0.) # mu, margin

ctrl.createContactTask("CRF0", rname+".r_foot", lgsm.Displacement(lgsm.vector(-.039,-.027, .031), RotRZdown), 1.5, 0.) # mu, margin
ctrl.createContactTask("CRF1", rname+".r_foot", lgsm.Displacement(lgsm.vector(-.039, .027, .031), RotRZdown), 1.5, 0.) # mu, margin
ctrl.createContactTask("CRF2", rname+".r_foot", lgsm.Displacement(lgsm.vector(-.039, .027,-.099), RotRZdown), 1.5, 0.) # mu, margin
ctrl.createContactTask("CRF3", rname+".r_foot", lgsm.Displacement(lgsm.vector(-.039,-.027,-.099), RotRZdown), 1.5, 0.) # mu, margin



##### SET TASK CONTROLLERS
CoMTask     = ctrl.createCoMTask("com", "XY", 10., kp=0.) #, kd=0.
ctrl.task_updater.register( xic.task_controller.ZMPController( CoMTask, dynModel, [[-0.03,0.02]], RonQ=1e-6, horizon=1.8, dt=dt, H_0_planeXY=lgsm.Displacement(), stride=3, gravity=9.81) )


##### OBSERVERS
from observers import CoMPositionObserver
cpobs = CoMPositionObserver(dynModel, wm.phy, wm.icsync)
cpobs.s.start()


##### SIMULATE
ctrl.s.start()

wm.startAgents()
wm.phy.s.agent.triggerUpdate()

#import dsimi.interactive
#dsimi.interactive.shell()()
time.sleep(10.)

wm.stopAgents()
ctrl.s.stop()



##### RESULTS
cpobs.s.stop()

cpobs.plot()


