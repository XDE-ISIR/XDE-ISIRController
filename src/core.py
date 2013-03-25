#!/xde

""" Module to make a proxy of the orcisir_ISIRController based on the orc framework.

orcisir_ISIRController can be found in "https://hotline.isir.upmc.fr/wsvn/EReval?".
The operations proposed by the controller and the tasks managment may not be
well documented, and there may be lack of flexibility (e.g. no default values).

To overcome that, proxy methods are defined in a python class which derived from
dsmi.rtt.Task, with more flexibility on parameter definition.

Finally, task instances are separated from the controller to facilitate their use.
"""

import deploy.deployer as ddeployer
import dsimi.rtt

import lgsm





################################################################################
################################################################################
################################################################################
class ISIRCtrl(dsimi.rtt.Task):
    """ Proxy of orcisir_ISIRController.
    """

    def __init__(self, libdir, dynamic_model, robotName, physic_agent, sync_connector=None, solver="quadprog", useReducedProblem=False):
        """ Instantiate proxy of controller.
        
        :param libdir: path string where one can find the lib 'orcisir_Orocos_IsirController-gnulinux'
        :param dynamic_model: xde.DynamicModel instance built based on the controlled robot
        :param robotState_prefix: the prefix string given to the OConnectorRobotState linked with the robot
        :param robotJointTorque_prefix: the prefix string given to the IConnectorRobotJointTorque linked with the robot
        :param sync_connector: the synchronisation connector when this is required (in the WorldManager package, it is WorldManager.icsync)
        :param solver: a string to choose the internal solve; for now "quadprog" or "qld"
        """
        orocos_ICTask = ddeployer.load("oIT", "Orocos_ISIRController",
                                       module="orcisir_Orocos_IsirController-gnulinux", prefix="",
                                       libdir=libdir)
        super(ISIRCtrl, self).__init__(orocos_ICTask)
        
        # set dynamic model and init inner solver
        self.dynamic_model = dynamic_model
        self.s.setDynModelPointerStr(str(self.dynamic_model.this.__long__()), solver, useReducedProblem) #or "qld" or "quadprog"
        
        self.NDOF0 = 6
        if self.dynamic_model.hasFixedRoot():
            self.NDOF0 = 0

        # create connector in the physical agent: out.connector for robot state, and in.connector for tau
        robotPrefix = robotName+"_"
        physic_agent.s.Connectors.IConnectorRobotJointTorque.new(robotName+".ict", robotPrefix, robotName)
        physic_agent.s.Connectors.OConnectorRobotState.new(robotName+".ocpos", robotPrefix, robotName)

        # set connection from physic to controller
        physic_agent.getPort(robotPrefix+"q").connectTo(self.getPort("q"))
        physic_agent.getPort(robotPrefix+"qdot").connectTo(self.getPort("qDot"))
        physic_agent.getPort(robotPrefix+"Hroot").connectTo(self.getPort("Hroot"))
        physic_agent.getPort(robotPrefix+"Troot").connectTo(self.getPort("Troot"))
        physic_agent.getPort("contacts").connectTo(self.getPort("contacts"))

        # set connection from controller to physic
        if sync_connector is not None:
            sync_connector.addEvent(robotPrefix+"tau")
        self.getPort("tau").connectTo(physic_agent.getPort(robotPrefix+"tau"))



    ########################################################################
    # Methods to easily access operations saved in the ISIRController Task #
    ########################################################################
    def setJointLimits(self, lower_bounds, upper_bounds):
        """ Set the joint limits for the associated constraint.
        
        :param lower_bounds: list of lower limits, dim=model.nbInternalDofs()
        :param upper_bounds: list of upper limits, dim=model.nbInternalDofs()
        """
        self.s.setJointLimits(lgsm.vector(lower_bounds), lgsm.vector(upper_bounds))

    def setJointLimitsHorizonOfPrediction(self, horizon):
        """ Set the horizon of prediction (in second) for the joint limit constraint. """
        self.s.setJointLimitsHorizonOfPrediction(horizon)

    def setTorqueLimits(self, torque_limits):
        """ Set the torque limits for the associated constraint.
        
        :param torque_limits: torque limits, dim=model.nbInternalDofs()
        """
        self.s.setTorqueLimits(lgsm.vector(torque_limits))

    def setContactAvoidanceHorizonOfPrediction(self, horizon):
        """ Set the horizon of prediction (in second) for the contact avoidance constraint. """
        self.s.setContactAvoidanceHorizonOfPrediction(horizon)

    def setContactAvoidanceMargin(self, margin):
        """ Set the horizon of prediction (in second) for the contact avoidance constraint. """
        self.s.setContactAvoidanceMargin(margin)

    def setFixedRootPosition(self, H_root):
        """ Set the root position when the robot has a fixed base.
        
        When you change the root position of a fixed robot with method 'set_H_root_bm' for instance,
        the modification is not taken into account in your dynamic model saved in the controller.
        This can lead to miscalculation when updating task and constraints.
        To take into account this modification, you must update your model with method 'setFreeFlyerPosition',
        or you must use this method.
        
        :param H_root: a lgsm.Displacement which represent the root position from ground
        """
        self.s.setFixedRootPosition(H_root)



    ##################################
    # Methods to easily create tasks #
    ##################################
    def createFullTask(self, name, weight=1., level=0):
        """ Create a task that control the full state of the model.
        
        Generally, to set a reference posture of the robot.
        
        :param name: the unique name (id) of the task
        :param weight: the task weight for control trade-off when some tasks are conflicting
        :param level: the task priority for solver; low-leveled task are resolved first
        
        :rtype: a ISIRTask instance which give access to the task methods and bypass the controller
        """
        index = self.s.createFullTask(name)
        return ISIRTask(self, name, index, ISIRTask.FULLTASK, weight, level)

    def createPartialTask(self, name, dofs, weight=1., level=0):
        """ Create a task that control some state of the model.
        
        Generally, to control a particular subset of the robot, e.g. the arm, the leg, the spine...
        
        :param name: the unique name (id) of the task
        :param dofs: list of int (segment index) or string (segment name) corresponding to the controlled dofs.
                     Note that if you use a list of int, you must shift the segment indexes by 6 when the robot has a free flying root.
                     It also means that the free floating pose can be controlled.
        :param weight: the task weight for control trade-off when some tasks are conflicting
        :param level: the task priority for solver; low-leveled task are resolved first
        
        :rtype: a ISIRTask instance which give access to the task methods and bypass the controller
        """
        dofs_index = []
        for d in dofs:
            if isinstance(d, int):
                dofs_index.append(d)
            else:
                d_idx = self.dynamic_model.getSegmentIndex(d)
                dofs_index.append(self.NDOF0 + d_idx)

        index = self.s.createPartialTask(name, dofs_index)
        return ISIRTask(self, name, index, ISIRTask.PARTIALTASK, weight, level)

    def createFrameTask(self, name, segmentName, H_segment_frame, dofs, weight=1., level=0):
        """ Create a task that control a frame of the model.
        
        Generally to track a pose or a trajectory in the cartesian space.
        
        :param name: the unique name (id) of the task
        :param segmentName: the segment name that is rigidly linked with the controlled frame
        :param H_segment_frame: the lgsm.Displacement from the origin of the segment to the frame
        :param dofs: a string representing the controlled part of the frame, e.g. the rotation or the X & Y axis.
                     dofs is the combination of the following character (in this order): 'R', 'X', 'Y', 'Z'
        :param weight: the task weight for control trade-off when some tasks are conflicting
        :param level: the task priority for solver; low-leveled task are resolved first
        
        :rtype: a ISIRTask instance which give access to the task methods and bypass the controller
        """
        index = self.s.createFrameTask(name, segmentName, lgsm.Displacement(H_segment_frame), dofs.upper())
        return ISIRTask(self, name, index, ISIRTask.FRAMETASK, weight, level)

    def createCoMTask(self, name, dofs, weight=1., level=0):
        """ Create a task that control the Center of Mass (CoM) of the model.
        
        Generally associated to any balancing control, walking, static equilibrium etc...
        
        :param name: the unique name (id) of the task
        :param dofs: a string representing the controlled part of the CoM (here rotation control is meaningless)
                     it is the combination of the following character (in this order): 'X', 'Y', 'Z'
        :param weight: the task weight for control trade-off when some tasks are conflicting
        :param level: the task priority for solver; low-leveled task are resolved first
        
        :rtype: a ISIRTask instance which give access to the task methods and bypass the controller
        """
        index = self.s.createCoMTask(name, dofs.upper())
        return ISIRTask(self, name, index, ISIRTask.COMTASK, weight, level)

    def createContactTask(self, name, segmentName, H_segment_frame, mu, margin=0., weight=1., level=0):
        """ Create a task for frictional interaction with the environment.
        
        :param name: the unique name (id) of the task
        :param segmentName: the segment name that is rigidly linked with the contact frame
        :param H_segment_frame: the lgsm.Displacement from the origin of the segment to the frame
        :param mu: the Coulomb coefficient of friction
        :param margin: margin associated to the friction cone constraint. Positive margin means a thiner cone.
        :param weight: the task weight for control trade-off when some tasks are conflicting
        :param level: the task priority for solver; low-leveled task are resolved first
        
        :rtype: a ISIRTask instance which give access to the task methods and bypass the controller
        """
        index = self.s.createContactTask(name, segmentName, lgsm.Displacement(H_segment_frame), mu, margin)
        return ISIRTask(self, name, index, ISIRTask.CONTACTTASK, weight, level)



    ###################################
    # Methods for contact information #
    ###################################
    def addContactInformation(self, phy_outContactPort, ctrl_inPortName, segmentName):
        """ Add contact information in the solver to update contact task/constraints.
        
        :param phy_outContactPort: the dsimi.rtt.OutputPort which will transmit the contact information from physic agent
        :param ctrl_inPortName: the name of the input port that will receive the contact information into the controller
        :param segmentName: the segment name on which applies the contact information
        """
        self.s.addContactInformation(ctrl_inPortName, segmentName)
        phy_outContactPort.connectTo(self.getPort(ctrl_inPortName))

    def useContactInformation(self, ctrl_inPortName, isUsed):
        """ Define if a contact information port is used for obstacle avoidance.
        
        :param ctrl_inPortName: the name of the input port that will receive the contact information into the controller
        :param isUsed: enable/disable contact information
        """
        self.s.useContactInformation(ctrl_inPortName, isUsed)

    ##########################
    # Enable/Disable methods #
    ##########################
    def enableJointLimits(self, enabled):
        """ Enable/disable the joint limits constraint. """
        self.s.enableJointLimits(enabled)

    def enableTorqueLimits(self, enabled):
        """ Enable/disable the torque limits constraint. """
        self.s.enableTorqueLimits(enabled)

    def enableContactAvoidance(self, enabled):
        """ Enable/disable the contact avoidance constraint. """
        self.s.enableContactAvoidance(enabled)





################################################################################
################################################################################
################################################################################

class ISIRTask(object):
    """ Proxy of ISIRTask defined in the module 'orcisir_Orocos_IsirController-gnulinux'.
    
    This allows to bypass the controller when updating the task. A task instance which is
    separated from the controller gives simpler methods and leads to clearer code.
    """
    
    FULLTASK    = "fullTask"
    PARTIALTASK = "partialTask"
    FRAMETASK   = "frameTask"
    COMTASK     = "CoMTask"
    CONTACTTASK = "contactTask"
    
    def __init__(self, ctrl, name, index, taskType, weight=1., level=0):
        """ Instantiate a proxy of an ISIRTask.
        
        Warning: when creating this proxy the task must have been registred by the controller before.
        
        :param ctrl: the controller in which the task has been registered
        :param name: the unique name (id) of the task
        :param taskType: the ISIRTask.TYPE of the task, which can be one of the following:
                         FULLTASK, PARTIALTASK, FRAMETASK, COMTASK, CONTACTTASK
        :param weight: the task weight for control trade-off when some tasks are conflicting
        :param level: the task priority for solver; low-leveled task are resolved first
        """
        self.ctrl     = ctrl
        self.name     = name
        self.index    = index
        self.taskType = taskType
        
        print "TASK", name, ":", index
        
        self.setWeight(weight)
        self.setLevel(level)
        
        self.dimension = self.ctrl.s.getTaskDimension(self.index)
        
        self.updateTaskFunction = None
        if taskType   == self.FULLTASK:
            self.updateTaskFunction = self.ctrl.s.updateFullTask
        elif taskType == self.PARTIALTASK:
            self.updateTaskFunction = self.ctrl.s.updatePartialTask
        elif taskType == self.FRAMETASK:
            self.updateTaskFunction = self.ctrl.s.updateFrameTask
        elif taskType == self.COMTASK:
            self.updateTaskFunction = self.ctrl.s.updateCoMTask

    def setKpKd(self, kp, kd=None):
        """ Set the proportionnal (kp) and derivative (kd) gains of the task.
        
        :param kp: the proportionnal gain
        :param kd: the derivative gain. Note that if kd is None, then kd become 2.*sqrt(kp)
        """
        if kd is None:
            kd = 2.*lgsm.math.sqrt(kp)
        self.ctrl.s.setTaskKpKd(self.index, kp, kd)

    def setWeight(self, weight):
        """ Set task weight """
        self.ctrl.s.setTaskWeight(self.index, weight)

    def setLevel(self, level):
        """ Set task level """
        self.ctrl.s.setTaskLevel(self.index, level)

    def activateAsObjective(self):
        """ Set task as an objective, meaning that an error may occur """
        self.ctrl.s.activateTaskAsObjective(self.index)

    def activateAsConstraint(self):
        """ Set task as a constraint, meaning that no error should occur """
        self.ctrl.s.activateTaskAsConstraint(self.index)

    def deactivate(self):
        """ Deactive objectives and constraints linked to the task """
        self.ctrl.s.deactivateTask(self.index)

    def update(self, posDes, velDes, accDes=None):
        """ Update the desired values tracked by the task.
        
        :param posDes: a lgsm.Displacement or lgsm.vector representing the desired pose, depending on the taskType
        :param velDes: a lgsm.Twist or lgsm.vector representing the desired velocity, depending on the taskType
        :param accDes: a lgsm.Twist or lgsm.vector representing the reference acceleration, depending on the taskType.
                       If accDes is None, reference acceleration becomes null.
        """
        if accDes is None:
            accDes = lgsm.zero(self.dimension)
        self.updateTaskFunction(self.index, posDes, velDes, accDes)


    def getError(self):
        """ get the tracking proportional error (the position error)
        
        :rtype: a lgsm.vector of position error
        """
        return self.ctrl.s.getTaskError(self.index)

    def getErrorDot(self):
        """ get the tracking derivative error (the velocity error)
        
        :rtype: a lgsm.vector of velocity error
        """
        return self.ctrl.s.getTaskErrorDot(self.index)



