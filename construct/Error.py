# -*- coding: utf-8 -*-

#from gmpy2 import mpfr, get_context
# import gmpy2
# with gmpy2.local_context():
# 	ctxInf = gmpy2.set_context(gmpy2.context(), precision=100, round=RoundDown)
# 	ctxSup = gmpy2.set_context(gmpy2.context(), precision=100, round=RoundUp)


class Error(object):
	"""Class for error evaluation"""

	#----------------------------------------------------------------------
	def __init__(self , mode="truncature", lsb=None , rshift=None):
		self._mode = mode
		if lsb!=None and rshift!= None:
			if mode == "truncature":
				# inf and sup bounds for errors interval
				#self._inf = mpfr(-2**( lsb)) + mpfr( 2**(lsb-rshift) )
				self._inf = -2**( lsb) +  2**(lsb-rshift)
				self._sup = 0
				# mean and variance for noise evaluation
				self._mean = 2**( lsb - 1)* (1 - 2**(- rshift))
				self._variance = (2**( 2*lsb)/ 12) * (1-2**(2*-rshift))
			else: # nearest round-off
				self._inf = -2**( lsb-1)+2**(lsb-rshift)
				self._sup = 2**( lsb-1)
				self._mean = 2**( lsb - rshift - 1)
				self._variance = (2**( 2*lsb)/ 12) * (1-2**(2*-rshift))
		else: # !! No one of lsb & rshift is given
			self._inf = 0
			self._sup = 0
			self._mean = 0
			self._variance = 0
			
	@property
	def moments(self):
		return self._mean, self._variance
	
	@property
	def inter(self):
		return self._inf, self._sup
	
	@property
	def mean(self):
		return self._mean
	@mean.setter
	def mean(self,m):
		self._mean = m
		
	@property
	def variance(self):
		return self._variance
	@variance.setter
	def variance(self,v):
		self._variance = v
		
	@property
	def inf(self):
		return self._inf
	@inf.setter
	def inf(self,i):
		self._inf = i
	
	@property
	def sup(self):
		return self._sup
	@sup.setter
	def sup(self,s):
		self._sup = s
	
	def __iadd__(self,other):
		"""Override of '+=' operation permits us to write 'current_error += Error(lsb=l, rshift=d)' for errors propagation"""
		self._inf += other._inf
		self._sup += other._sup
		self._mean += other._mean
		self._variance += other._variance
		return self
	
	def __repr__(self):
		return "("+repr(self._mean)+" , "+repr(self._variance)+")"