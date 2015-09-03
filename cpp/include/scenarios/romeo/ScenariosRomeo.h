#ifndef SCENARIOSROMEO_H
#define SCENARIOSROMEO_H

#include "wocra/Tasks/wOcraTaskSequenceBase.h"
#include "wocra/Models/wOcraModel.h"

class ScenarioRomeo_Balance: public wocra::wOcraTaskSequenceBase
{
    public:
        ScenarioRomeo_Balance();
        virtual ~ScenarioRomeo_Balance();
    protected: 
        virtual void doInit(wocra::wOcraController& ctrl, wocra::wOcraModel& model);
        virtual void doUpdate(double time, wocra::wOcraModel& state, void** args); 
    private:
        // Full posture task
        wocra::wOcraFullPostureTaskManager*            tmFull;
        // Partial torso posture task
        wocra::wOcraPartialPostureTaskManager*         tmPartialTorso;
        // Left foot contact task
        wocra::wOcraContactSetTaskManager*             tmFootContactLeft;
        // Right foot contact task
        wocra::wOcraContactSetTaskManager*             tmFootContactRight;
        // CoM task
        wocra::wOcraCoMTaskManager*                    tmCoM;
        // Segment body task
        wocra::wOcraSegOrientationTaskManager*         tmSegOrientationBody;
        // Segment left foot task
        wocra::wOcraSegPoseTaskManager*                tmSegPoseFootLeft;
        // Segment right foot task
        wocra::wOcraSegPoseTaskManager*                tmSegPoseFootRight;
};

#endif // TASKSETROMEOBALANCE_H
