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
wm.createAllAgents(dt, lmd_max=.01, uc_relaxation_factor=0.01)
wm.resizeWindow("mainWindow",  640, 480, 1000, 50)


##### GROUND
groundWorld = xrl.createWorldFromUrdfFile(xr.ground, "ground", [0,0,0,1,0,0,0], True, 0.001, 0.001)
wm.addWorld(groundWorld)


##### ROBOT
rname = "robot"
fixed_base = False
robotWorld = xrl.createWorldFromUrdfFile(xr.icub_simple, rname, [0.5,0.5,0.6,0,0,0,1], fixed_base, .003, 0.001)
wm.addWorld(robotWorld)
robot = wm.phy.s.GVM.Robot(rname)
robot.enableGravity(True)
N  = robot.getJointSpaceDim()

dynModel = xrl.getDynamicModelFromWorld(robotWorld)
jmap     = xrl.getJointMapping(xr.icub_simple, robot)


##### SET INTERACTION
wm.ms.setContactLawForMaterialPair("material.metal", "material.concrete", 2, 2.5)
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


#robot.setJointPositionsMin(-10*lgsm.ones(N))
#robot.setJointPositionsMax(-10*lgsm.ones(N))


##### CTRL
import xde_isir_controller as xic
ctrl = xic.ISIRController(dynModel, rname, wm.phy, wm.icsync, "qld", True)

#### SET CONSTRAINTS
torqueConst = ctrl.add_constraint(xic.TorqueLimitConstraint(ctrl.getModel(), 80.*lgsm.ones(N) ) )
jointConst  = ctrl.add_constraint(xic.JointLimitConstraint(ctrl.getModel(), .2 ) )


##### SET TASKS
fullTask = ctrl.createFullTask("full", w=0.0001, kp=9., q_des=qinit)

#waistTask   = ctrl.createFrameTask("waist", rname+'.waist', lgsm.Displacement(), "RZ", w=10.0, kp=25., pose_des=lgsm.Displacement(0,0,.58,0,0,0,1))

back_dofs   = [jmap[rname+"."+n] for n in ['torso_pitch', 'torso_roll', 'torso_yaw']]
backTask    = ctrl.createPartialTask("back", back_dofs, w=1.0, kp=25., q_des=lgsm.zeros(3))


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

#for c in l_contacts + r_contacts:
#    c.activateAsConstraint()
#    c.setWeight(10.)


##### SET TASK CONTROLLERS
RotLZUp = lgsm.Quaternion(-sqrt2on2,0.0,-sqrt2on2,0.0) * lgsm.Quaternion(0.0,0.0,0.0,1.0)
RotRZUp = lgsm.Quaternion(0.0, sqrt2on2,0.0, sqrt2on2) * lgsm.Quaternion(0.0,0.0,0.0,1.0)
H_lf_sole = lgsm.Displacement([-.039, 0, .034]+RotLZUp.tolist() )
H_rf_sole = lgsm.Displacement([-.039, 0,-.034]+RotRZUp.tolist() )
walkingActivity = xic.walk.WalkingActivity( ctrl, dt,
                                    rname+".l_foot", H_lf_sole, l_contacts,
                                    rname+".r_foot", H_rf_sole, r_contacts,
                                    rname+'.waist', lgsm.Displacement(0,0,0,0,0,0,1), lgsm.Displacement(0,0,.58,1,0,0,0),
                                    H_0_planeXY=lgsm.Displacement(0,0,0.002,1,0,0,0), weight=10., contact_as_objective=True)

walkingActivity.stayIdle()


##### OBSERVERS
zmplipmpobs = ctrl.add_updater( xic.observers.ZMPLIPMPositionObserver(ctrl.getModel(), lgsm.Displacement(), dt, 9.81) )


##### SIMULATE
ctrl.s.start()

wm.startAgents()
wm.phy.s.agent.triggerUpdate()

#import xdefw.interactive
#xdefw.interactive.shell_console()()
time.sleep(2.)
print "WALK .5m front"

zmp_ref = walkingActivity.goTo([.5,0.], relative_pos=True)

walkingActivity.wait_for_end_of_walking()
time.sleep(.5)

print "WALK .5m front and .1m left"
zmp_ref = walkingActivity.goTo([.5,0.1], relative_pos=True)

walkingActivity.wait_for_end_of_walking()
time.sleep(.5)

print "WALK 1m front and .4m left"
zmp_ref = walkingActivity.goTo([1.,0.4], relative_pos=True)

walkingActivity.wait_for_end_of_walking()
time.sleep(.5)

wm.stopAgents()
ctrl.s.stop()



##### RESULTS
import pylab as pl
zmplipm = zmplipmpobs.get_record()
pl.plot(zmplipm)
pl.plot(zmp_ref, ls=":")
pl.show()


