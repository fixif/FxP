# -*- coding: utf-8 -*-
from copy import deepcopy
from copy import copy
from string import Template
from FPF import FPF
from Error import Error
from math import log, ceil, floor
import os.path
import string

from Adder import Adder
from Constant import Constant
from Variable import Variable	
	
	
class Multiplier(object):
	"""Classe pour les multiplieurs"""
	
	formatting = False
	
	#----------------------------------------------------------------------
	def __init__(self,cst_val,wl_cst, var_inter, var_name, mult_wl, index, signed=True,RndOff = None, lsb_final=0):
		self._name = "Mult_"+var_name
		
		# Tree arguments
		self._result = None #father
		self._index = index
		self._label = 1
		
		# Constant
		self._cst_bs = Constant(cst_val, wl_cst, signed=signed)
		self._cst = Constant(cst_val, wl_cst, signed=signed)	
		
		# Variable
		self._var = var_inter
		self._var_name = var_name
		
		# Shift and Noise
		
		#self._wl = (self._cst_bs.FxPF.msb + self._var.FxPF.msb +2 -lsb_final) if Multiplier.formatting else mult_wl
		self._wl = mult_wl
		self._lsb_final=lsb_final
		self._rshift_cst = 0
		self._rshift = 0
		self._local_error = Error()
		self._total_error = Error()
		self._RndOff = RndOff or "RAM"
		
		# Result
		self._var_result = None
		self.Calc_var_result()
		
		
	@property
	def wl(self):
		return self._wl

	@property
	def constant(self):	
		return self._cst
	
	@property
	def variable(self):
		return self._var
	
	@property
	def result(self):
		return self._var_result
	
	@property
	def _left(self):
		return self
		
	def __ge__(self,other):
		"""override of the greater or equal operation"""
		#print self._left._index, other._left._index
		return self._left._index >= other._left._index
	
	def __repr__(self):
		return "%s, lsb = %d"%(self._name, self.result.FPF.lsb)
	
	def cmp_lsb(self, other):
		mi = self.result.FPF.lsb
		mj = other.result.FPF.lsb
		return mi - mj
	
	def Calc_var_result(self):
		if Multiplier.formatting :
			self._var_result, self._rshift = self._var.mult(self._cst , lsb = self._lsb_final)
		else:
			self._var_result, self._rshift = self._var.mult(self._cst , wl = self._wl)
		self._local_error = Error(lsb=self._var_result.FPF.lsb, rshift=self._rshift)
		# je copie _local_error dans _total_error pour les oSoPs à un seul produit
		self._total_error = Error(lsb=self._var_result.FPF.lsb, rshift=self._rshift)
		self._rshift_cst = -self._cst.FPF.lsb + self._cst_bs.FPF.lsb
		

	def insert_on_top(self, other):
		pass

	def add(self,other, options=None):
		"""Merge two Multipliers with an Adder"""
		if isinstance(other,Adder):
			print "Grosse panique"
			pass
		#addition d'un multiplier et d'un multiplier
		adder = Adder()
		adder._nll += 1
		adder._nrl += 1
		#adder._expr = "(M+M)"
		adder._operands=[self,other]
		adder._left = self
		adder._top = True
		if options != None:
			adder.Calc_var_result(options)
		return adder
	
	def Code_fixe(self,osop):
		return "(%d * %s)"%(self._cst.mantissa, self._var_name)
	
	
	### Code functions ###
	
	
	def Tikz(self,osop,tab):
		rshift_add = self._result._rshift[self._result._operands.index(self)]
		rshift_mult = self._rshift
		
		code = "\t"*tab+"child{[sibling distance=1cm"
		#if (rshift_mult > 0) and (rshift_add == 0) :
		if (rshift_mult > 0) and ((self.result.FPF.wml() == self._result._var_op[self._result._operands.index(self)].FPF.wml()) or Multiplier.formatting ==True) :
			code += ", level distance=0cm"
		code +="]\n"
		
		# shift computed to align FxPF for addition
		#if rshift_add != 0:
		if self.result.FPF.wml() != self._result._var_op[self._result._operands.index(self)].FPF.wml() and Multiplier.formatting ==False:
			tab += 1
			#code += "\t"*tab+"node(D"+repr(self).translate(None,string.punctuation)+") [dec%d] {$%s"%(rshift_add >0 and 1 or 2,rshift_add >0 and ">>" or "<<")+repr(abs(rshift_add))+" $}\n"
			code += "\t"*tab+"node(D"+repr(self).translate(None,string.punctuation)+") [form] {$F$}\n"
			if rshift_mult > 0:
				code += "\t"*tab+"child{[level distance=0.0cm]\n"
			else:
				code += "\t"*tab+"child{[level distance=0.4cm]\n"
		
		# multiplication shift
		if rshift_mult > 0:
			tab += 1
			code += "\t"*tab+"node(D"+repr(self).translate(None,string.punctuation)+"_M) [decM] {$\\gg %d $}\n"%(rshift_mult)
			code += "\t"*tab+"child{[level distance=0.4cm]\n"
		code += "\t"*(tab+1)+"node("+repr(self).translate(None,string.punctuation)+") [mult] {$\\times$}\n"
		code += "\t"*(tab+1)+"child{\n"
		
		# Constant (and possible constant shift) (node and label)
		if self._rshift_cst != 0:
			tab += 1
			code += "\t"*(tab+1)+"node(DC"+repr(self).translate(None,string.punctuation)+") [form] {$F$}\n"
			code += "\t"*(tab+1)+"child{\n"
		if self._cst.FPF.wl:
			code += "\t"*(tab+2)+"node(Cst%d) [cst] {%d}\n"%(self._index,self._cst.mantissa)
			code += "\t"*(tab+1)+"edge from parent node[left] {%s}\n"%self._cst_bs.FPF+"\t"*(tab+1)+"}\n"
		else:
			code += "\t"*(tab+2)+"node(Cst%d) [cst] {%f}\n"%(self._index,self._cst_val)
			code += "\t"*(tab+1)+"edge from parent node[left] {%s}\n"%self._cst_bs.FPF+"\t"*(tab+1)+"}\n"
		if self._rshift_cst != 0:
			code += "\t"*tab+"edge from parent node[left] {%s}\n"%self._cst.FPF
			code += "\t"*tab+"}\n"
			tab -= 1
		
		# Variable (node and label)
		code += "\t"*(tab+1)+"child{\n"+"\t"*(tab+2)+"node(Var%d) [var] {$%s$}\n"%(self._index,self._var_name)
		code += "\t"*(tab+1)+"edge from parent node[right] {%s}\n"%self._var.FPF+"\t"*(tab+1)+"}\n"
		
		if rshift_mult > 0:
			code += "\t"*(tab)+"}\n"
			tab -= 1				
		#if rshift_add != 0:
		if self.result.FPF.wml() != self._result._var_op[self._result._operands.index(self)].FPF.wml() and Multiplier.formatting ==False:
			if (self == self._result._operands[0]) and (len(self._result._operands) == 2) :
				code += "\t"*(tab+1)+"edge from parent node[left] {%s}\n"%self._var_result.FPF
			else:
				code += "\t"*(tab+1)+"edge from parent node[right] {%s}\n"%self._var_result.FPF
			code += "\t"*tab+"}\n"
			tab -= 1
		#FxPF label after adder shift
		if (self == self._result._operands[0]) and (len(self._result._operands) == 2) :
			code += "\t"*(tab+1)+"edge from parent node[left,sloped,above] {%s}\n"%self._result._var_op[0].FPF
		else:
			code += "\t"*(tab+1)+"edge from parent node[right,sloped,above] {%s}\n"%self._result._var_op[1].FPF
		code += "\t"*tab+"}\n"
		return code, 1.5
	
	
	def Code_C(self,i,n):
		if Multiplier.formatting:
			st_fix = "\t//Computation of c%d*v%d in sd\n"%(self._index, self._index)
		else:
			st_fix = "\t//Computation of c%d*v%d in register r%d\n"%(self._index, self._index, i)
		st_sample = ""
		st_acf_dec = "ac_fixed<%d,%d,true,AC_TRN> v%d,"%(self._var.FPF.wl,self._var.FPF.msb+1,self._index)
		#Déclaration de la constante
		st_fix += "\tac_fixed<%d,%d,true,AC_TRN> c%d = %.53g;\n"%(self._cst_bs.FPF.wl,self._cst_bs.FPF.msb+1,self._index,self._cst_bs.approx)
		#Calcul du produit
		if Multiplier.formatting:
			st_fix += "\tsd = sd + c%d*v%d;\n"%(self._index,self._index)
		else:
			st_fix += "\tac_fixed<%d,%d,true,AC_TRN> r%d = c%d*v%d;\n\n"%(self._var_result.FPF.wl,self._var_result.FPF.msb+1,i,self._index,self._index)
		#st_fix += '\tcout<<"r%d = "<< c%d << " * "<< v%d <<" = "<<r%d<<endl;\n\n'%(i,self._index,self._index,i)
		return st_fix, st_acf_dec, st_sample, i+1,n+1

	def Code_C_int(self,R):
		i = 0
		while R[i]: i=i+1
		# i est l'indice du premier registre non utilisé
		st_fix = "\t// Computation of c%d*v%d in r%d\n"%(self._index, self._index,i)
		st_fix += "\tr%d = %d*v%d"%(i, self._cst_bs.mantissa, self._index)
		if self._rshift > 0:
			st_fix += ">> %d"%(self._rshift)
		st_fix += ";\n"
		R[i] = 1 #le registre i est désormais utilisé
		return st_fix, R, i
	
	def Code_reel(self, L = None,i = None):
		if L:
			return self._cst_bs.value * L[i], str(self._cst_bs.value)+" * "+str(L[i]), i+1
		else:
			return "%.53g * v%d"%(self._cst_bs.approx,self._index)	



# WTF ??
# class Multiplier2(object):
# 	"""Classe pour les multiplieurs"""
	
# 	formatting = False
	
# 	#----------------------------------------------------------------------
# 	def __init__(self,cst_val,wl_cst, var_inter, var_name, mult_wl, index, signed=True,RndOff = None, lsb_final=0):
# 		self._name = "Mult_"+var_name
		
# 		# Tree arguments
# 		self._result = None #father
# 		self._index = index
# 		self._label = 1
		
# 		# Constant
# 		self._cst_bs = Constant(cst_val, wl_cst, signed=signed)
# 		self._cst = Constant(cst_val, wl_cst, signed=signed)	
		
# 		# Variable
# 		self._var = var_inter
# 		self._var_name = var_name
		
# 		# Shift and Noise
		
# 		self._wl = (self._cst_bs.FxPF.msb + self._var.FxPF.msb +2 -lsb_final) if Multiplier2.formatting else mult_wl
# 		self._rshift_cst = 0
# 		self._rshift = 0
# 		self._local_error = Error()
# 		self._RndOff = RndOff or "RAM"
		
# 		# Result
# 		self._var_result = None
# 		self.Calc_var_result()
		
		
# 	@property
# 	def wl(self):
# 		return self._wl

# 	@property
# 	def constant(self):	
# 		return self._cst
	
# 	@property
# 	def variable(self):
# 		return self._var
	
# 	@property
# 	def result(self):
# 		return self._var_result
	
# 	@property
# 	def _left(self):
# 		return self
		
# 	def __ge__(self,other):
# 		"""override of the greater or equal operation"""
# 		#print self._left._index, other._left._index
# 		return self._left._index >= other._left._index
	
# 	def __repr__(self):
# 		return "%s, lsb = %d"%(self._name, self.result.FxPF.lsb)
	
# 	def cmp_lsb(self, other):
# 		mi = self.result.FxPF.lsb
# 		mj = other.result.FxPF.lsb
# 		return mi - mj
	
# 	def Calc_var_result(self):
# 		self._var_result, self._rshift = self._var.mult(self._cst , self._wl)
# 		self._local_error = Error(lsb=self._var_result.FxPF.lsb, rshift=self._rshift)
# 		self._rshift_cst = -self._cst.FxPF.lsb + self._cst_bs.FxPF.lsb
		
# 	def add(self,other, options=None):
# 		"""Merge two Multipliers with an Adder"""
# 		if isinstance(other,Adder2):
# 			print "Grosse panique"
# 			pass
# 		#addition d'un multiplier et d'un multiplier
# 		adder = Adder2()
# 		#adder._nb_leaves += 2
# 		#adder._expr = "(M+M)"
# 		adder._operands=[self,other]
# 		adder._left = self
# 		adder._top = True
# 		if options != None:
# 			adder.Calc_var_result(options)
# 		return adder
