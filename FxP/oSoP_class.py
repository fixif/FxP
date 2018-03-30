# -*- coding: utf-8 -*-
from copy import deepcopy
from copy import copy
from string import Template
from FPF import FPF
from Error import Error
from math import log, ceil
import cPickle, os.path, pickle, string

from Constant import Constant
from Adder import Adder
from Multiplier import Multiplier


class oSoP(object):
	"""ordered Sum-of-Products class"""

	#----------------------------------------------------------------------
	def __init__(self, top, var_final=None):
		"""Constructeur"""
		self._Top = top
		if isinstance(top,Multiplier):
			self._var_final = top._var_result
		else:
			self._var_final = var_final
		#self._var_test= self._Top._var_result.copy()
		self._rshift_final = 0

		

	def height(self):
		"""Retourne la profondeur d'osop"""
		if isinstance(self._Top, Adder):
			return self._Top.height()
		else:
			return 1

	def insert_leaf(i, cur_m):
		node = self._Top
		for j in range(i):
			node = node._operands[1]
		new_adder = Adder([node,cur_m])
		if i==0:
			self._Top = new_adder
			new_adder._top = True
			node._top = False 
		else:
			node._result._operands[1] = new_adder
		node._result = new_adder
		cur_m._result = new_adder



	def Calc_var_result(self, options):
		alfix, plus, msb_final = options
		#print self._Top._var_result.FxPF	, self._Top._var_result.integers
		self._rshift_final = max(-self._Top._var_result.lsb + self._var_final.lsb,0)
		self._var_final._integer_inf = self._Top._var_result._integer_inf>>self._rshift_final
		self._var_final._integer_sup = self._Top._var_result._integer_sup >> self._rshift_final
		self._var_final.values = self._Top._var_result.values
		if self._rshift_final > 0:
			error = Error(lsb=self._var_final.lsb , rshift=self._rshift_final)
			self._Top._local_error += error
			self._Top._total_error += error
		# TODO : RBM
		
	def Code(self, TYPE, indice=None,FILE = None, name=None):
		#self.ReOrder()
		if TYPE == "fix":
			#Écrit la somme correspondant à l'oSoP self en ligne, avec les décalages
			pass
			#print self._Top.Code_fixe(self)
		
		elif TYPE == "real":
			if isinstance(self._Top, Adder):
				self._Top.Result_builder() #Reconstruction des peres
				self._Top.label_builder() #Construction des labels de Sethi-Ullman
			if FILE:
				fichier = open(FILE, "r")
				L = []
				for line in fichier:
					L.append(float(line)*2**-11)
				print self._Top.Code_reel(L,0)[0],self._Top.Code_reel(L,0)[1]
			else:
				return self._Top.Code_reel()
		
		#elif TYPE == "algo":
			#return self._Top.Algo(self,1)
		
		#elif TYPE == "falgo":
			#return self._Top.Algo_fix(self,1)
		
		elif TYPE == "Tikz":
			#Génère le code TikZ représentant l'oSoP self, dans le fichier code.tex
			file_in = open("Templates/code_tmplt.tex", 'r')
			if indice != None:
				if name:
					file_out = open("Generated/LaTeX/%s/bis/code%d.tex"%(name,indice), 'w')
				else:
					file_out = open("Generated/LaTeX/ss6/code%d.tex"%(indice), 'w')
			else:
				file_out = open("Generated/LaTeX/code.tex", 'w')
			tmplt = Template(file_in.read())
			if isinstance(self._Top, Adder):
				self._Top.Result_builder() #Reconstruction des peres
			code, width = self._Top.Tikz(self,0)
			d = dict(TP_code = code)
			file_out.write(tmplt.safe_substitute(d))
			file_in.close()
			file_out.close()
			
		elif TYPE == "C":
			#Génère les codes C pour calculer la somme induite par l'oSoP self
			if isinstance(self._Top, Adder):
				self._Top.Result_builder() #Reconstruction des peres
				self._Top.label_builder() #Construction des labels de Sethi-Ullman
			
			#Generation du code C utilisant la librairie ac_fixed dans le fichier code.cpp
			code_acf_sop,code_acf_dec, code_sample, i,n = self._Top.Code_C(0,0)
			code_acf_dec = code_acf_dec[:-1] #enleve la virgule en trop

			#dec ac_fix
			code_acf_dec_S = ""
			if isinstance(self._Top, Adder):
				code_acf_dec_S += "\t//Declaration of sums sd and s\n\tac_fixed<%d,%d,true> sd = 0;\n\t"%(self._var_final.FPF.wl+self._rshift_final,self._var_final.FPF.msb+1)
				code_acf_dec_S += "ac_fixed<%d,%d,true> s = 0;\n"%(self._var_final.FPF.wl,self._var_final.FPF.msb+1)
				code_acf_dec_out = "ac_fixed<%d,%d,true>"%(self._var_final.FPF.wl,self._var_final.FPF.msb+1)
			else:
				code_acf_dec_S += "\t//Declaration of sums sd and s\n\tac_fixed<%d,%d,true> sd = 0;\n\t"%(self._Top.result.FPF.wl,self._Top.result.FPF.msb+1)
				code_acf_dec_S += "ac_fixed<%d,%d,true> s = 0;\n"%(self._Top.result.FPF.wl,self._Top.result.FPF.msb+1)
				code_acf_dec_out = "ac_fixed<%d,%d,true>"%(self._Top.result.FPF.wl,self._Top.result.FPF.msb+1)


			if self._rshift_final > 0 or isinstance(self._Top, Multiplier):
				code_acf_sop += "\n\t//Computation of the final right shift\n"
				code_acf_sop += "\ts = s + sd;\n\treturn s;"
				#code_acf_sop += "\tac_fixed<%d,%d,true,AC_TRN> r%d = r%d;\n"%(self._var_final.FxPF.wl,self._var_final.FxPF.msb+1,i,i-1)
				#code_acf_sop += "\tdouble res = r%d.to_double();\n\treturn res;"%(i)
			file_in = open("Templates/code_tmplt.c", 'r')
			if indice != None:
				if name:
					file_out = open("Generated/Code/%s/bis/code%d.c"%(name,indice), 'w')
				else:
					file_out = open("Generated/Code/ss6/code%d.c"%(indice), 'w')
			else:
				file_out = open("Generated/Code/code.c", 'w')
			tmplt = Template(file_in.read())
			
			#Génération du code C entier dans le fichier code.cpp
			if isinstance(self._Top, Adder):
				R=[None]*(self._Top._label) #liste des registres nécessaires (minimum) pour le code entier
			else :
				R=[None]
			#-->code_int_sop récupère le code correspondant au calcul
			#-->code_int_dec récupère les déclarations des variables
			code_int_sop, R, i = self._Top.Code_C_int(R)
			code_int_sop +="\t// The result is returned "
			if self._rshift_final > 0 :
				code_int_sop += "with a final right shift\n"
			i_res = None
			for j in range(len(R)):
				if R[j] != None:
					i_res = j
					break
			code_int_sop += "\n\treturn r%d"%(i_res)
			if self._rshift_final > 0 :
				code_int_sop += " >> %d"%(self._rshift_final)
			code_int_sop += ";"
				
			
			#Génération du code C flottant
			code_float = "r = "+self.Code("real")
			code_float += ";\n\treturn r;"
			st_afg_flt = ""
			st_arg = ""
			for i in range(n):
				st_arg += "int16_t v%d"%(i)
				st_afg_flt += "double v%d"%(i)
				if i<n-1:
					st_arg +=","
					st_afg_flt +=","
			d = dict(TP_Int_sop = code_int_sop,TP_acf_sop = code_acf_sop,TP_acf_dec_var_out = code_acf_dec_out, TP_acf_dec_S = code_acf_dec_S, TP_acf_dec_var = code_acf_dec, TP_Float_sop = code_float,TP_Size =st_arg,TP_Size_FLT=st_afg_flt)
			file_out.write(tmplt.safe_substitute(d))
			file_in.close()
			file_out.close()
		else:
			return "Faut pas deconner y'en a assez la je crois"	
		
		
	def ReOrder(self):
		self._Top.reorder()
					
	#def quantized(self):
		#L = []
		#for M in self._Multipliers:
			#v = M._fpf_cst.approx(M._cst_val)
			#if v==0:
				#print "Warning : Underflow in constant %s"%M
		#return [M._fpf_cst.approx(M._cst_val) for M in self._Multipliers ]
