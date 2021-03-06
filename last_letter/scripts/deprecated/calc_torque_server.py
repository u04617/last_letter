#!/usr/bin/env python

import rospy
from math import pow
from math import pi
from math import sin
from math import cos
from last_letter.srv import *
import tf.transformations
from geometry_msgs.msg import Vector3


def calc_torque_callback(req):

	states = req.states
	inputs = req.inputs

	#Request air data from getAirData server
	airdata = getAirData(states)
	airspeed = airdata.airspeed
	alpha = airdata.alpha
	beta = airdata.beta
	#rospy.logerr('airspeed:%g, alpha:%g, beta:%g',airspeed, alpha, beta)#

	#Split Control input values
	deltaa = inputs[0]
	deltae = inputs[1]
	deltat = inputs[2]
	deltar = inputs[3]

	#Read from parameter server
	rho = rospy.get_param('world/rho')
	c = rospy.get_param('airframe/c')
	b = rospy.get_param('airframe/b')
	s = rospy.get_param('airframe/s')
	c_l_0 = rospy.get_param('airframe/c_l_0')
	c_l_b = rospy.get_param('airframe/c_l_b')
	c_l_p = rospy.get_param('airframe/c_l_p')
	c_l_r = rospy.get_param('airframe/c_l_r')
	c_l_deltaa = rospy.get_param('airframe/c_l_deltaa')
	c_l_deltar = rospy.get_param('airframe/c_l_deltar')
	c_m_0 = rospy.get_param('airframe/c_m_0')
	c_m_a = rospy.get_param('airframe/c_m_a')
	c_m_q = rospy.get_param('airframe/c_m_q')
	c_m_deltae = rospy.get_param('airframe/c_m_deltae')
	c_n_0 = rospy.get_param('airframe/c_n_0')
	c_n_b = rospy.get_param('airframe/c_n_b')
	c_n_p = rospy.get_param('airframe/c_n_p')
	c_n_r = rospy.get_param('airframe/c_n_r')
	c_n_deltaa = rospy.get_param('airframe/c_n_deltaa')
	c_n_deltar = rospy.get_param('airframe/c_n_deltar')
	k_t_p = rospy.get_param('motor/k_t_p')
	k_omega = rospy.get_param('motor/k_omega')
	
	#Read angular rates
	(p, q, r) = (states.twist.twist.angular.x, states.twist.twist.angular.y, states.twist.twist.angular.z)
	
	#Calculate Aerodynamic torque
	qbar = 1.0/2*rho*pow(airspeed,2)*s #Calculate dynamic pressure
	if airspeed==0:
		(la, ma, na) = (0, 0, 0)
	else:
		la = qbar*b*(c_l_0 + c_l_b*beta + c_l_p*b*p/(2*airspeed) + c_l_r*b*r/(2*airspeed) + c_l_deltaa*deltaa + c_l_deltar*deltar)
		ma = qbar*c*(c_m_0 + c_m_a*alpha + c_m_q*c*q/(2*airspeed) + c_m_deltae*deltae)
		na = qbar*b*(c_n_0 + c_n_b*beta + c_n_p*b*p/(2*airspeed) + c_n_r*b*r/(2*airspeed) + c_n_deltaa*deltaa + c_n_deltar*deltar)
	
	#Calculate Thrust torque
	lm = -k_t_p*pow(k_omega*deltat,2)
	mm = 0
	nm = 0	

	#Sum torques
	l = la + lm
	m = ma + mm
	n = na + nm	

	response = Vector3(l, m, n)
	
	return response

def getAirData(Odo):
    rospy.wait_for_service('calc_air_data')
    try:
        calcAirData = rospy.ServiceProxy('calc_air_data',calc_air_data)
        return calcAirData(Odo.twist.twist.linear)
    except rospy.ServiceException, e:
		rospy.logerr("Service call failed: %s"%e)

def getLiftAlpha(alpha):
	rospy.wait_for_service('c_lift_a')
	try:
		calcLiftAlpha = rospy.SericeProxy('c_lift_a',c_lift_a)
		return calcLiftAlpha(alpha)
	except rospy.ServiceException, e:
		rospy.logerr("Service call failed: %s"%e)

def getDragAlpha(alpha):
	rospy.wait_for_service('c_drag_a')
	try:
		calcDragAlpha = rospy.SericeProxy('c_drag_a',c_drag_a)
		return calcDragAlpha(alpha)
	except rospy.ServiceException, e:
		rospy.logerr("Service call failed: %s"%e)


if __name__=='__main__':
	try:
		rospy.init_node('calc_torque_server')
		s = rospy.Service('calc_torque', calc_torque, calc_torque_callback)
		rospy.loginfo('calc_torque service running')
		while not rospy.is_shutdown():
			rospy.spin()
				
	except rospy.ROSInterruptException:
		pass	
