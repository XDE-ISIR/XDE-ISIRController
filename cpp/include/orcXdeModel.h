#ifndef ORCXDEMODEL_H
#define ORCXDEMODEL_H

#include "wocra/Models/wOcraModel.h"
#include <Python.h>
#include <dictobject.h>

#define FREE_ROOT_DOF 6
#define COM_POS_DIM 3
#define TRANS_ROT_DIM 6

#include <xdecore/gvm.h>
#include <xdecore/gvm/DynamicModel.h>

class orcXdeModel: public wocra::wOcraModel
{
public:

//===========================Constructor/Destructor===========================//
    orcXdeModel(xde::gvm::extra::DynamicModel* xdeModel, std::string rname, PyDictObject* jointList);
    virtual ~orcXdeModel();

//=============================General functions==============================//
    virtual int                          nbSegments               () const;
    virtual const Eigen::VectorXd&       getActuatedDofs          () const;
    virtual const Eigen::VectorXd&       getJointLowerLimits      () const;
    virtual const Eigen::VectorXd&       getJointUpperLimits      () const;
    virtual const Eigen::VectorXd&       getJointPositions        () const;
    virtual const Eigen::VectorXd&       getJointVelocities       () const;
    virtual const Eigen::Displacementd&  getFreeFlyerPosition     () const;
    virtual const Eigen::Twistd&         getFreeFlyerVelocity     () const;

//=============================Dynamic functions==============================//
    virtual const Eigen::MatrixXd&       getInertiaMatrix         () const;
    virtual const Eigen::MatrixXd&       getInertiaMatrixInverse  () const;
    virtual const Eigen::MatrixXd&       getDampingMatrix         () const;
    virtual const Eigen::VectorXd&       getNonLinearTerms        () const;
    virtual const Eigen::VectorXd&       getLinearTerms           () const;
    virtual const Eigen::VectorXd&       getGravityTerms          () const;

//===============================CoM functions================================//
    virtual double                                         getMass            () const;
    virtual const Eigen::Vector3d&                         getCoMPosition     () const;
    virtual const Eigen::Vector3d&                         getCoMVelocity     () const;
    virtual const Eigen::Vector3d&                         getCoMJdotQdot     () const;
    virtual const Eigen::Matrix<double,3,Eigen::Dynamic>&  getCoMJacobian     () const;
    virtual const Eigen::Matrix<double,3,Eigen::Dynamic>&  getCoMJacobianDot  () const;

//=============================Segment functions==============================//
    virtual const Eigen::Displacementd&                    getSegmentPosition          (int index) const;
    virtual const Eigen::Twistd&                           getSegmentVelocity          (int index) const;
    virtual double                                         getSegmentMass              (int index) const;
    virtual const Eigen::Vector3d&                         getSegmentCoM               (int index) const;
    virtual const Eigen::Matrix<double,6,6>&               getSegmentMassMatrix        (int index) const;
    virtual const Eigen::Vector3d&                         getSegmentMomentsOfInertia  (int index) const;
    virtual const Eigen::Rotation3d&                       getSegmentInertiaAxes       (int index) const;
    virtual const Eigen::Matrix<double,6,Eigen::Dynamic>&  getSegmentJacobian          (int index) const;
    virtual const Eigen::Matrix<double,6,Eigen::Dynamic>&  getSegmentJdot              (int index) const;
    virtual const Eigen::Matrix<double,6,Eigen::Dynamic>&  getJointJacobian            (int index) const;
    virtual const Eigen::Twistd&                           getSegmentJdotQdot          (int index) const;

    void printAllData();

protected:

//===========================Update state functions===========================//
    virtual void                doSetJointPositions     (const Eigen::VectorXd& q);
    virtual void                doSetJointVelocities    (const Eigen::VectorXd& dq);
    virtual void                doSetFreeFlyerPosition  (const Eigen::Displacementd& Hroot);
    virtual void                doSetFreeFlyerVelocity  (const Eigen::Twistd& Troot);

//============================Index name functions============================//
    virtual int                 doGetSegmentIndex       (const std::string& name) const;
    virtual const std::string&  doGetSegmentName        (int index) const;
    virtual int                 doGetDofIndex           (const std::string& name) const;
    virtual const std::string&  doGetDofName            (int index) const;
    virtual const std::string   doSegmentName           (const std::string& name) const;
    virtual const std::string   doDofName               (const std::string& name) const;

private:
    xde::gvm::extra::DynamicModel* _m;
    PyDictObject* _jointList;
    Eigen::VectorXd _actuatedDofs;
    Eigen::VectorXd _linearTerms;
    std::vector< std::string > _segmentName;
};


#endif
