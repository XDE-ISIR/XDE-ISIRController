#!/xde

import xde_world_manager as xwm
import xde_robot_loader  as xrl
import xde_resources     as xr
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
robotWorld = xrl.createWorldFromUrdfFile(xr.icub_simple, rname, [0,0,0.6,1,0,0,0], fixed_base, 0.001, 0.001)
wm.addWorld(robotWorld)
robot = wm.phy.s.GVM.Robot(rname)
robot.enableGravity(True)
N  = robot.getJointSpaceDim()

dynModel = xrl.getDynamicModelFromWorld(robotWorld)
jmap     = xrl.getJointMapping(xr.icub_simple, robot)


##### SET INTERACTION
wm.ms.setContactLawForMaterialPair("material.metal", "material.concrete", 1, 1.5)
robot.enableContactWithBody("ground.ground", True)
wm.contact.showContacts([(rname+"."+b,"ground.ground") for b in ["l_foot", "r_foot"]]) # to display contact


##### SET INITIAL STATE
qinit = lgsm.zeros(N)
for name, val in [("l_elbow_pitch", pi/8.), ("r_elbow_pitch", pi/8.), ("l_knee", -0.05), ("r_knee", -0.05), ("l_ankle_pitch", -0.05), ("r_ankle_pitch", -0.05), ("l_shoulder_roll", pi/8.), ("r_shoulder_roll", pi/8.)]:
    qinit[jmap[rname+"."+name]] = val

robot.setJointPositions(qinit)
dynModel.setJointPositions(qinit)
robot.setJointVelocities(lgsm.zeros(N))
dynModel.setJointVelocities(lgsm.zeros(N))


##### CTRL
import xde_isir_controller as xic
ctrl = xic.ISIRController(dynModel, rname, wm.phy, wm.icsync, "quadprog", True)


##### SET TASKS
fullTask = ctrl.createFullTask("full", w=0.0001, kp=9., q_des=qinit)
waistTask   = ctrl.createFrameTask("waist", rname+'.waist', lgsm.Displacement(), "RXYZ", w=1., kp=36., pose_des=lgsm.Displacement(0,0,.58,1,0,0,0))
back_dofs   = [jmap[rname+"."+n] for n in ['torso_pitch', 'torso_roll', 'torso_yaw']]
backTask    = ctrl.createPartialTask("back", back_dofs, w=0.001, kp=16., q_des=lgsm.zeros(3))

sqrt2on2 = lgsm.np.sqrt(2.)/2.
RotLZdown = lgsm.Quaternion(-sqrt2on2,0.0,-sqrt2on2,0.0) * lgsm.Quaternion(0.0,1.0,0.0,0.0)
RotRZdown = lgsm.Quaternion(0.0, sqrt2on2,0.0, sqrt2on2) * lgsm.Quaternion(0.0,1.0,0.0,0.0)


i=0
l_contacts = []
r_contacts = []
for y in [-.027, .027]:
    for z in [-.031, .099]:
        ct = ctrl.createContactTask("CLF"+str(i), rname+".l_foot", lgsm.Displacement([-.039, y, z]+RotLZdown.tolist()), 1.5)
        l_contacts.append(ct)
        ct = ctrl.createContactTask("CRF"+str(i), rname+".r_foot", lgsm.Displacement([-.039, y,-z]+RotRZdown.tolist()), 1.5)
        r_contacts.append(ct)
        i+=1


##### SIMULATE
ctrl.s.start()

wm.startAgents()
wm.phy.s.agent.triggerUpdate()


for i in range(1000):
    for t in l_contacts+r_contacts:
        print t.getName(), t.getComputedForce().transpose() # the force should be expressed in the task space
    time.sleep(.1)


wm.stopAgents()
ctrl.s.stop()


