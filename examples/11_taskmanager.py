#!/xde


import xde_world_manager as xwm
import xde_robot_loader  as xrl
import xde_resources     as xr
import lgsm
import time


##### AGENTS
dt = 0.01
wm = xwm.WorldManager()
wm.createAllAgents(dt, lmd_max=.2)
wm.resizeWindow("mainWindow",  640, 480, 1000, 50)


##### ROBOT
rname = "kuka"
robotWorld = xrl.createWorldFromUrdfFile(xr.kuka, rname, [0,0,0,1,0,0,0], True, 0.001, 0.01, use_collada_color=False)
wm.addWorld(robotWorld)
robot = wm.phy.s.GVM.Robot(rname)
robot.enableGravity(True)
N = robot.getJointSpaceDim()

dynModel = xrl.getDynamicModelFromWorld(robotWorld)


##### CTRL
import xde_isir_controller  as xic
dynModel2 = xic.getModelFromSharedLibrary("resources/libModelKukaFixed.so", "Create_kukafixed", rname)


ctrl = xic.ISIRController(dynModel, rname, wm.phy, wm.icsync, "quadprog", True)
#ctrl = xic.ISIRController(dynModel2, rname, wm.phy, wm.icsync, "quadprog", False)


#gposdes = 1.2 * lgsm.ones(N)
#gveldes = lgsm.zeros(N)
#fullTask = ctrl.createFullTask("full", "INTERNAL", w=1., kp=20.)
#fullTask.set_q(gposdes)
#fullTask.set_qdot(gveldes)

taskmanager = xic.TaskXMLParser("resources/fulljointcontrol1.xml", ctrl.controller)
taskdesc = xic.fullstateCast(taskmanager.getTaskdesc("full"))
trajXML = xic.trajectoryReaderFullJointCast( taskmanager.getTrajectoryReader("full_pos"))
ctrl.add_updater(trajXML)


##### OBSERVERS
#jpobs = ctrl.add_updater(xic.observers.JointPositionsObserver(ctrl.getModel()))

###### SIMULATE
ctrl.s.start()

wm.startAgents()
wm.phy.s.agent.triggerUpdate()

#import xde_isir_controller.task_gui as xicgui
#xicgui.configure()
#xicgui.createTaskGui(fullTask)

#time.sleep(5.)

#wm.stopAgents()
#ctrl.s.stop()



##### RESULTS
#import pylab as pl

#jpos = jpobs.get_record()
#pl.plot(jpos)
#pl.show()


import xdefw.interactive
xdefw.interactive.shell_console()()