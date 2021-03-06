#include "sequences/icub/examples_basic/02_squatting.h"
#include <cmath>

#ifndef PI
#define PI 3.1415926
#endif

Sequence_iCub_02_Squatting::Sequence_iCub_02_Squatting() : wocra::wOcraTaskSequenceBase()
{
}

Sequence_iCub_02_Squatting::~Sequence_iCub_02_Squatting()
{
}

void Sequence_iCub_02_Squatting::doInit(wocra::wOcraController& ctrl, wocra::wOcraModel& model)
{
    // Initialise full posture task
    Eigen::VectorXd q_full = Eigen::VectorXd::Zero(model.nbInternalDofs());
    q_full[model.getDofIndex("l_elbow_pitch")] = PI/8.0;
    q_full[model.getDofIndex("r_elbow_pitch")] = PI/8.0;
    q_full[model.getDofIndex("l_knee")] = -0.05;
    q_full[model.getDofIndex("r_knee")] = -0.05;
    q_full[model.getDofIndex("l_ankle_pitch")] = -0.05;
    q_full[model.getDofIndex("r_ankle_pitch")] = -0.05;
    q_full[model.getDofIndex("l_shoulder_roll")] = PI/8.0;
    q_full[model.getDofIndex("r_shoulder_roll")] = PI/8.0;

    taskManagers["tmFull"] = new wocra::wOcraFullPostureTaskManager(ctrl, model, "fullPostureTask", ocra::FullState::INTERNAL, 9.0, 2*sqrt(9.0), 0.0001, q_full, false);

    // Initialise waist pose
    taskManagers["tmSegPoseWaist"] = new wocra::wOcraSegPoseTaskManager(ctrl, model, "waistPoseTask", "waist", ocra::XYZ, 36.0, 2*sqrt(36.0), 1.0, Eigen::Displacementd(0.0,0.0,0.58,-M_SQRT1_2,0.0,0.0,M_SQRT1_2), false);
    tmSegPoseWaist = dynamic_cast<wocra::wOcraSegPoseTaskManager*>(taskManagers["tmSegPoseWaist"]);

    // Initialise partial posture task
    Eigen::VectorXi sdofs(3);
    sdofs << model.getDofIndex("torso_pitch"), model.getDofIndex("torso_roll"), model.getDofIndex("torso_yaw");
    Eigen::VectorXd zero = Eigen::VectorXd::Zero(3);

    taskManagers["tmPartialBack"] = new wocra::wOcraPartialPostureTaskManager(ctrl, model, "partialPostureBackTask", ocra::FullState::INTERNAL, sdofs, 16.0, 2*sqrt(16.0), 0.001, zero, false);

    double mu_sys = 0.5;
    double margin = 0.0;

    double sqrt2on2 = sqrt(2.0)/2.0;
    Eigen::Rotation3d rotLZdown = Eigen::Rotation3d(-sqrt2on2, 0.0, -sqrt2on2, 0.0) * Eigen::Rotation3d(0.0, 1.0, 0.0, 0.0);
    Eigen::Rotation3d rotRZdown = Eigen::Rotation3d(0.0, sqrt2on2, 0.0, sqrt2on2) * Eigen::Rotation3d(0.0, 1.0, 0.0, 0.0);

    // Initialise left foot contacts
    std::vector<Eigen::Displacementd> LFContacts;
    LFContacts.push_back(Eigen::Displacementd(Eigen::Vector3d(-.039,-.027,-.031), rotLZdown));
    LFContacts.push_back(Eigen::Displacementd(Eigen::Vector3d(-.039, .027,-.031), rotLZdown));
    LFContacts.push_back(Eigen::Displacementd(Eigen::Vector3d(-.039, .027, .099), rotLZdown));
    LFContacts.push_back(Eigen::Displacementd(Eigen::Vector3d(-.039,-.027, .099), rotLZdown));

    taskManagers["tmFootContactLeft"] = new wocra::wOcraContactSetTaskManager(ctrl, model, "leftFootContactTask", "l_foot", LFContacts, mu_sys, margin, false);

    // Initailise right foot contacts
    std::vector<Eigen::Displacementd> RFContacts;
    RFContacts.push_back(Eigen::Displacementd(Eigen::Vector3d(-.039,-.027, .031), rotRZdown));
    RFContacts.push_back(Eigen::Displacementd(Eigen::Vector3d(-.039, .027, .031), rotRZdown));
    RFContacts.push_back(Eigen::Displacementd(Eigen::Vector3d(-.039, .027,-.099), rotRZdown));
    RFContacts.push_back(Eigen::Displacementd(Eigen::Vector3d(-.039,-.027,-.099), rotRZdown));

    taskManagers["tmFootContactRight"] = new wocra::wOcraContactSetTaskManager(ctrl, model, "RightFootContactTask", "r_foot", RFContacts, mu_sys, margin, false);
}

void Sequence_iCub_02_Squatting::doUpdate(double time, wocra::wOcraModel& state, void** args)
{
    std::cout << "time: " << time << std::endl;

    double z0 = 0.55;
    double A = 0.02;
    double T = 5.0;
    double phi = 0.0;
    double omega = 2*PI/T;
    double z = z0 + A * sin(omega * time + phi);
    double z_dot = omega * A * cos(omega * time + phi);
    double z_ddot = - omega * omega * A * sin(omega * time + phi);

    Eigen::Displacementd x = Eigen::Displacementd(0.0, 0.0, z, -M_SQRT1_2, 0.0, 0.0, M_SQRT1_2);
    Eigen::Twistd x_d = Eigen::Twistd(0.0, 0.0, z_dot, 0.0, 0.0, 0.0);
    Eigen::Twistd x_dd = Eigen::Twistd(0.0, 0.0, z_ddot, 0.0, 0.0, 0.0);
    tmSegPoseWaist->setState(x, x_d, x_dd);
}
