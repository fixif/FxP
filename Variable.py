# -*- coding: utf-8 -*-

"""
The Variable class allows to represent variables in fixed-point arithmetic
"""

from fipogen.FxP import FPF
from fipogen.FxP import Constant
from math import floor, log

########################################################################
class Variable(object):
	"""Variable class to store FxP variables
	
	Attributes:
		fpf: fixed-point format (FxPF object)
		integer_inf, integer_sup: lower and upper bounds of the integer associated value
		value_inf, value_sup: lower and upper bounds of the variable
		name: name of the variable
		"""
	
	#test
	formatting = False
	variableCount = 0

	#----------------------------------------------------------------------
	def __init__(self, value_inf = None, value_sup = None, wl = None, signed = None , fpf = None, integer_inf = None, integer_sup = None, name=None):
		"""Construct a Variable object :
		- compute integer values and FxPF from value_inf, value_sup, wl, signed
		- compute integer values from value_inf, value_sup, fpf
		- compute nothing from value_inf, value_sup, integer_inf, integer_sup, fpf (wl is fpf.wl)
		- compute all values (real and integer) from fpf


		X = Variable( value_inf=..., value_sup=..., wl=...)
		X = Variable( value_inf=..., value_sup=..., wl=..., signed=...)
		X = Variable( value_inf=..., value_sup=..., fpf=...)
		X = Variable( value_inf=..., value_sup=..., fpf=..., integer_inf=..., integer_sup=...)
		X = Variable( fpf=...)


		"""
		# check for good combination of given arguments
		#TODO: assert or raise error ?
		if not ((value_inf is not None and value_sup is not None and wl and not (signed or fpf or integer_inf or integer_sup)) \
					or (value_inf is not None and value_sup is not None and wl and signed is not None and not (fpf or integer_inf or integer_sup)) \
					or (value_inf is not None and value_sup is not None and fpf and integer_inf is not None and integer_sup is not None and not (wl or (signed is not None))) \
					or (value_inf is not None and value_sup is not None and fpf and not (wl or (signed is not None) or integer_inf or integer_sup)) \
					or (fpf and not (value_inf or value_sup or wl or (signed is not None) or integer_inf or integer_sup))):
			raise ValueError("Bad combination of arguments")
		
		# check for non-sense values
		if fpf:
			if signed is not None and (signed is not fpf._signed):
				raise ValueError( "Conflict between Signed and Unsigned !!")	
			if wl and (fpf.wl != wl): # normally never happens (wl and fpf)
				raise ValueError( "Conflict between wordlengths !!")
			# and so on
			wl = fpf.wl 
			signed = fpf._signed
			
		# default sign is True
		if signed is None and fpf is None :
			signed=True
		
		if fpf and not (value_inf or value_sup or integer_inf or integer_sup): # if only a FxPF is given
			self._FPF = fpf
			# compute integer values from fpf
			self._integer_inf = fpf._signed and int(-2**(fpf.wl-1)) or 0
			self._integer_sup = fpf._signed and int(2**(fpf.wl-1) - 1) or int((2**fpf.wl) - 1)

		elif fpf and value_inf and value_sup and integer_inf and integer_sup:
			# nothing to do in this case
			self._integer_inf = int(integer_inf)
			self._integer_sup = int(integer_sup)
			self._FPF = fpf

		elif fpf: # if not only a FxPF is given
			# compute (with Constant class) integer value and FxPF of each real value
			if value_inf == 0:
				c_sup = Constant(value_sup, signed = signed, fpf = fpf)
				self._integer_inf = 0
				self._integer_sup = int(integer_sup) or int(c_sup.mantissa)
			elif value_sup == 0:
				c_inf = Constant(value_inf, signed = signed, fpf = fpf)
				self._integer_inf = int(integer_inf) or int(c_inf.mantissa)
				self._integer_sup = 0
			else:
				#HACK à la con pour séance BenThib020316
				try:
					c_inf = Constant(value_inf, signed = signed, fpf = fpf)
				except:
					c_inf = Constant(-2**(fpf.msb-1), signed=signed, fpf=fpf)
				try:
					c_sup = Constant(value_sup, signed = signed, fpf = fpf)
				except:
					c_sup = Constant(2**(fpf.msb-1)-2**fpf.lsb, signed = signed, fpf = fpf)

				# if msb_inf != msb_sup
				if c_inf.FPF.msb < c_sup.FPF.msb:
					c_inf = Constant(value_inf,wl,signed,c_sup.FPF)
				elif c_inf.FPF.msb > c_sup.FPF.msb:
					c_sup = Constant(value_sup,wl,signed,c_inf.FPF)

				# if integer values are given then we select it, else we select the computed integer values from constants
				self._integer_inf = int(integer_inf) or int(c_inf.mantissa)
				self._integer_sup = int(integer_sup) or int(c_sup.mantissa)

			# if fpf is given then we select it, else we select the computed FxPF from constants
			self._FPF = fpf
		
		else: # case 1 or 2, no given fpf, just wl and possibly signed
			if value_inf == 0:
				c_sup = Constant(value_sup, signed = signed, wl = wl)
				self._integer_inf = 0
				self._integer_sup = int(integer_sup) or int(c_sup.mantissa)
				self._FPF = c_sup.FPF
			elif value_sup == 0:
				c_inf = Constant(value_inf, signed = signed, wl = wl)
				self._integer_inf = int(integer_inf) or int(c_inf.mantissa)
				self._integer_sup = 0
				self._FPF = c_inf.FPF
			else:
				c_inf = Constant(value_inf, signed = signed, wl = wl)
				c_sup = Constant(value_sup, signed = signed, wl = wl)
			
				# if msb_inf != msb_sup
				if c_inf.FPF.msb < c_sup.FPF.msb:
					c_inf = Constant(value_inf,wl,signed,c_sup.FPF)
				elif c_inf.FPF.msb > c_sup.FPF.msb:
					c_sup = Constant(value_sup,wl,signed,c_inf.FPF)

				# if integer values are given then we select it, else we select the computed integer values from constants
				self._integer_inf = integer_inf or c_inf.mantissa
				self._integer_sup = integer_sup or c_sup.mantissa

				self._FPF = c_sup.FPF

		# name
		if name:
			self._name = name
		else:
			self._name = 'Var'+str(Variable.variableCount)
			Variable.variableCount += 1

		# if real values are given then we select it, else we compute them from FxPF
		self._value_inf = value_inf or self._integer_inf * 2**self.FPF.lsb
		self._value_sup = value_sup or self._integer_sup * 2**self.FPF.lsb
		
	@property
	def integers(self):
		return self._integer_inf, self._integer_sup
	
	@property
	def FPF(self):
		return self._FPF
	@FPF.setter
	def FPF(self, fpf):
		self._FPF = fpf
	#TODO: on a le droit de modifier le FxPF ???????????
	#à supprimer

	
	@property
	def approx_values(self):
		return self._integer_inf*2**(self._FPF._lsb),self._integer_sup*2**(self._FPF._lsb)
	
	@property
	def values(self):
		return self._value_inf, self._value_sup
	@values.setter
	def values(self, t):
		assert isinstance(t,tuple) and len(t)==2, "argument for values is not a tuple of two terms"
		self._value_inf = t[0]
		self._value_sup = t[1]
		
	@property
	def lsb(self):
		return self._FPF._lsb
	
	def __repr__(self):
		return "[%g ; %g]"%(self.approx_values[0],self.approx_values[1])

	def copy(self):
		v_inf,v_sup = self.values
		N_inf,N_sup = self.integers
		w,m,l = self.FPF.wml()
		fpf = FPF(wl=w , msb=m , signed=self.FPF._signed)
		return Variable(value_inf=v_inf, value_sup=v_sup, fpf=fpf, integer_inf=N_inf, integer_sup=N_sup)
		
	def __rshift__(self, d):
		"""Apply a right shift of d bits onto integer values and FxPF of a copy of self."""
		SELF=self.copy()
		SELF._integer_inf >>= d
		SELF._integer_sup >>= d
		wl,m,lsb = SELF.FPF.wml()
		lsb = lsb + d
		SELF._FPF = FPF(wl=wl , lsb=lsb , signed = self.FPF._signed)
		return SELF
	
	def __lshift__(self, d):
		"""Apply a left shift of d bits onto integer values and FxPF of a copy of self."""
		SELF=self.copy()
		SELF._integer_inf <<= d
		SELF._integer_sup <<= d
		wl,m,lsb = SELF.FPF.wml()
		lsb = lsb - d
		SELF._FPF = FPF(wl=wl , lsb=lsb , signed = self.FPF._signed)
		return SELF	
	
	def Formatting(self,fpf):
		"""Format the variable self into the given format"""
		SELF = self.copy()
		rshift = 0
		if SELF.FPF.msb > fpf.msb:
			SELF._integer_inf %= 2**fpf.msb
			SELF._integer_sup %= 2**fpf.msb		
		if SELF.FPF.lsb < fpf.lsb:
			rshift = fpf.lsb - SELF.FPF.lsb
			SELF._integer_inf >>= rshift
			SELF._integer_sup >>= rshift
		elif SELF.FPF.lsb > fpf.lsb:
			if SELF._integer_inf == 0.:
				SELF._integer_inf = 0
				SELF._integer_sup=0
			SELF._integer_inf <<= SELF.FPF.lsb - fpf.lsb
			SELF._integer_sup <<= SELF.FPF.lsb - fpf.lsb	
		SELF.FPF = fpf
		return SELF, rshift

	def add(self,other,wl_op,msb_final=None, fpf_add= None):
		# if other is not a Variable object, then return an AssertionError
		assert (isinstance(other,Variable)), "Variable type expected for 'other', not %s"%type(other).__name__
		# the function computes sum between two variables where other variable has the smaller lsb,
		# then if it's not the case, addition is re-called with arguments interchanged
		if other.lsb < self.lsb:
			V , var1, var2, rshift= other.add(self,wl_op,msb_final= msb_final,fpf_add=fpf_add)
			return V, var2, var1, [rshift[1],rshift[0]]
		rshift = [0,0]
		SELF=self.copy()
		OTHER=other.copy()
		
		# 1. FxPF of addition
		if fpf_add :
			msb_add = min(max(SELF.FPF.msb,OTHER.FPF.msb), fpf_add.msb)
			if Variable.formatting is True:
				l_add = fpf_add.lsb
			else:
				l_add = msb_add - fpf_add.wl +1
			fpf_add = FPF(msb=msb_add, lsb=l_add, signed=fpf_add._signed)
		else: #normally never happens
			msb_add = max(SELF.FPF.msb,OTHER.FPF.msb)
			l_add = msb_add + 1 - wl_op
		
		# 2. Formatting of the two operands into the format of the addition
		# rshift is computed by this formatting
		SELF, rshift[0] = SELF.Formatting(fpf_add)
		OTHER, rshift[1] = OTHER.Formatting(fpf_add)
			
		# 3. Addition
		inf = SELF._integer_inf + OTHER._integer_inf
		sup = SELF._integer_sup + OTHER._integer_sup
		
		# 4. Overflow
		# in case of overflow for inf or sup, sums are recomputed with one bit shifted integers
		if ((inf < -2**(wl_op-1)) or (sup > 2**(wl_op-1)-1)):
			if	(msb_add == msb_final):
				inf = -2**(wl_op-1)
				sup = 2**(wl_op-1)-1
			else:
				SELF = SELF >> 1
				if OTHER != SELF:
					OTHER = OTHER >> 1
				inf = SELF.integers[0] + OTHER.integers[0]
				sup = SELF.integers[1] + OTHER.integers[1]
				l_add -= 1
			
		# the result Variable is created with real values, integer values and computed fpf (from wl_op and l_add)
		V = Variable(value_inf = SELF.values[0]+OTHER.values[0] , value_sup = SELF.values[1]+OTHER.values[1], fpf = fpf_add, integer_inf = inf , integer_sup = sup)
		# operands rshifts are computed as the difference between operand lsb and l_add if positive, 0 else

		return V, SELF, OTHER, rshift
	
	def mult(self,cst,wl=None,lsb = None):
		"""Multiplication between constant and variable on wl_op bits (for the wordlength)"""
		# if cst is not a Constant object, then return an AssertionError
		assert (isinstance(cst,Constant)), "Constant type expected for 'cst', not %s"%type(cst).__name__
		
	
		
		# compute real values
		X = (cst.value * self.values[0], cst.value * self.values[1])
		inf = min(X)
		sup = max(X)
		
		# compute msb
		
		if not Variable.formatting :
			# constant shift is computed as the difference between optimal wordlength (wl_cst + wl_var) and operator wordlength (wl_op)
			rshift = cst.FPF.wl + self.FPF.wl - wl
			# if rshift < 0 then rshift equals 0 (only positive shift is considered)
			rshift = max(rshift,0)

			# compute integer values with a positive (or zero) shift onto the constant
			#NX = ((cst.integer >> cst_rshift)*self.integers[0] , (cst.integer >> cst_rshift)*self.integers[1])
			NX = ((cst.mantissa * self.integers[0]) >> rshift , (cst.mantissa * self.integers[1]) >> rshift)
			# if cst.value > 0 then Ninf <-- NX[0], else Ninf <-- NX[1]. In both cases Ninf <-- min(NX)
			Ninf = min(NX)
			# same reasoning for Nsup, Nsup <-- max(NX)
			Nsup = max(NX)
			fpf = FPF(wl=wl , msb=cst.FPF.msb + self.FPF.msb + 1)
			V = Variable(value_inf = inf , value_sup = sup, fpf = fpf, integer_inf = int(Ninf) , integer_sup = int(Nsup))
		else:
			lsb_prod = cst.FPF._lsb + self.FPF._lsb
			rshift = max(lsb - lsb_prod,0)
			Cx = Constant(max(abs(inf),abs(sup)), wl = 16)
			wl = Cx.FPF._msb + 1-lsb
			V = Variable(value_inf = inf , value_sup = sup, wl = wl)
		return V, rshift




