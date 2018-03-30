# -*- coding: utf-8 -*-
from copy import deepcopy
from copy import copy
from Adder import Adder
from Multiplier import Multiplier
from oSoP_class import oSoP
from Variable import Variable
from FPF import FPF
from math import ceil, log, factorial, floor

	
	
def oSoP_Generator2(multipliers, max_lsb, fpf_add, var_final, alfix = False, plus = False, formatting = False):
	# args
	N=len(multipliers)
	if N==2:
		result = multipliers[0].add(multipliers[1],(alfix,plus,fpf_add))
		best_osop = oSoP(result, var_final)
		best_osop.Calc_var_result((alfix,plus,fpf_add))
	else:
		results = []
		stack = [ multipliers  ]
		

		nb=0
		m = len(stack)
		best_mean = 10000
		while stack:

			# get first possibility
			osops = stack.pop()

			# examin all the possibilities to take two of these osops that satisfies the constraint
			# i,j are the two examined osops (with i<j)
			for j in range(1,len(osops)):
				for i in range(j):
					# check if the constraint is ok
					if (osops[i] >= osops[0]) and (abs(osops[j].cmp_lsb(osops[i])) <= max_lsb+1):
					#if (osops[i] >= osops[0]):
						result = osops[:]
						# then we can add element i with element j
						op_j = result.pop(j)
						op_i = result.pop(i)
						result.insert( 0, op_i.add(op_j,(alfix,plus,fpf_add)) )
						#print len(result)
						
						# result is a final result or a partial result according to its length
						if len(result)==1:
							nb += 1
							if nb%100000==0:
								print nb
							# add it to the list of possibilities
							#we have an oSop
							osop = oSoP(result[0], var_final)
							
							#test (ligne de dessous en commentaire)
							osop.Calc_var_result((alfix,plus,fpf_add))
							#yield osop


							if formatting: 
								if osop.height() == int(ceil(log(N,2))):
									return osop

							else:
								if osop._Top._total_error.mean <= best_mean:
									if osop._Top._total_error.mean < best_mean:
										best_osop = osop
										best_mean = osop._Top._total_error.mean
									else:
										if osop.height() < best_osop.height():
											best_osop = osop
											best_mean = osop._Top._total_error.mean
								
								

						else:
							# or add this partial result to the stack (some of the osops are not yet used)
							stack.append( result)
	return best_osop
	
	
def oSoP_Generator_de_ouf(multipliers, max_lsb, fpf_add, var_final, alfix = False, plus = False):
	N=len(multipliers)
	L_mult = multipliers[:]

	op1 = L_mult.pop(0)
	op2 = L_mult.pop(0)
	restult = [oSoP(op1.add(op2,(alfix,plus,fpf_add)), var_final)]
	n=3

	#prev_m = op2
	while n != N :
		Res = []
		# je prend le multiplieur suivant dans ma liste
		current_m = L_mult.pop(0)
		for osop in restult :
			i=0
			cur_m = copy(current_m)
			
			T = deepcopy(osop)
			node = T._Top
			while node._nll > node._nrl:
				T.insert_leaf(i, cur_m)
				Res.append(T)
				i += 1
				T = deepcopy(osop)
				node = T._Top
				for j in range(i):
					node = node._operands[1]
				if isinstance(node, Multiplier):
					break
		result = Res
		n += 1

	# J'ai tous mes oSoPs dans result, faut que je trouve le meilleur niveau erreur
	best_mean = 10000
	for osop in result:
		if osop._Top._total_error.mean <= best_mean:
			if osop._Top._total_error.mean < best_mean:
				best_osop = osop
				best_mean = osop._Top._total_error.mean
			else: #if osop._Top._total_error.mean == best_mean:
				if osop.height() < best_osop.height():
					best_osop = osop
					best_mean = osop._Top._total_error.mean
	return best_osop


def best_oSoP_gen(variables_name, variables, constants, constants_wordlength, multipliers_wordlength,\
                  adders_wordlength, fpf_final, alfix = False,plus = False, RndOff = "RAM", formatting = True):
	
	# args
	N=len(constants)
	delta=0
	
	if formatting:
		Variable.formatting = True
		Adder.formatting = True
		Multiplier.formatting = True
		
		delta = int(ceil(log(N,2)))
		Adder.wl = adders_wordlength + delta
		multipliers_wordlength += delta
		lsb_final = fpf_final.lsb - delta
	else:
		Variable.formatting = False
		Adder.formatting = False
		Multiplier.formatting = False		
		lsb_final = 0
	
	if not isinstance(constants_wordlength,list):
		constants_wordlength = [constants_wordlength]*N
	if not isinstance(multipliers_wordlength,list):
		multipliers_wordlength = [multipliers_wordlength]*N
	if RndOff and (not isinstance(RndOff,list)):
		RndOff = [RndOff]*N
	if not isinstance(variables_name,list):
		variables_name = [variables_name+repr(i) for i in range(N)]	
	Adder.wl_add = adders_wordlength
	var_final = Variable(fpf = fpf_final)
	
	# Multipliers creation from args
	multipliers = [Multiplier(constants[i], constants_wordlength[i], variables[i], variables_name[i],\
	                          multipliers_wordlength[i], i, RndOff=RndOff[i], lsb_final=lsb_final) for i in range(N)]
	multipliers.sort(Multiplier.cmp_lsb)
	
	# Heuristic for non-exhaustive generation
	# Computation of max_lsb, the maximum difference of lsb between two consecutive multipliers (in the sorted list)
	max_lsb=0
	for i in range(N-1):
		max_lsb = max(max_lsb , abs(multipliers[i+1].result.lsb - multipliers[i].result.lsb))	
	
	best_osop = None
	h=N
	
	# formatting is the bits cleaning option
	if formatting:
		# Computation of fpf_add, ie fpf_final 'plus' delta bits considered for additions
		fpf_add = FPF(wl=fpf_final.wl+delta, msb=fpf_final.msb, lsb=fpf_final.lsb-delta, signed=fpf_final._signed)
		for L in oSoP_Generator2(multipliers, max_lsb, fpf_add, var_final, alfix = False,plus = False, formatting=formatting):
			if L.height() ==ceil(log(N,2)):
				h=L.height()
				best_osop = L
				break
		
	# if formatting == False we use default parameters
	else:
		fpf_add = FPF(wl=adders_wordlength, msb=fpf_final.msb)
		
		nb=0
		LT=[]
		best_mean = 10000
		for L in oSoP_Generator2(multipliers, max_lsb, fpf_add, var_final, alfix = False,plus = False, formatting=formatting):
			nb+=1
			if nb%10000 == 0:
				print nb
				#LT.append(L)
				#break
			if L._Top._total_error.mean <= best_mean:
				if L._Top._total_error.mean < best_mean:
					LT=[]
				LT.append(L)
				best_mean = L._Top._total_error.mean
				best_osop = L
		
		
		h = LT[0].height()
		for L in LT:
			if L.height() <=h:
				h=L.height()
				best_osop = L
		
	return best_osop




def best_oSoP_gen_from_dict(D):

	if isinstance(D,list):
		Osop =[]
		for i,d in enumerate(D):
			Osop.append(best_oSoP_gen_from_dict(d))
		return Osop
	else:
		variables = D["list_var"]
		constants = D["list_cst"]
		constants_wordlength = D["wl_cst"]
		multipliers_wordlength = D["wl_mult"]
		adders_wordlength = D["wl_add"]
		fpf_final = D["fpf_final"]
		formatting = D["formatting"]
		RndOff = "RAM"


		# args
		N=len(constants)
		delta=0
		
		if formatting:
			Variable.formatting = True
			Adder.formatting = True
			Multiplier.formatting = True
			
			if N==1:
				delta=0
			else:
				delta = int(floor(log(N-1,2)))+1
			Adder.wl = adders_wordlength + delta
			multipliers_wordlength += delta
			lsb_final = fpf_final.lsb - delta
		else:
			Variable.formatting = False
			Adder.formatting = False
			Multiplier.formatting = False		
			lsb_final = 0
			Adder.wl = adders_wordlength
		
		if not isinstance(constants_wordlength,list):
			constants_wordlength = [constants_wordlength]*N
		if not isinstance(multipliers_wordlength,list):
			multipliers_wordlength = [multipliers_wordlength]*N

		
		var_final = Variable(fpf = fpf_final)
		
		# Multipliers creation from args
		#Q&D
		multipliers=[]
		for i in range(N):
			M=None
			if constants_wordlength[i] >0:
				try:
					M=Multiplier(constants[i], constants_wordlength[i], variables[i], variables[i]._name,\
						multipliers_wordlength[i], i, RndOff=RndOff, lsb_final=lsb_final)
				except:
					print "Erreur création multiplieur"
			if M:
				multipliers.append(M)
		#multipliers = [Multiplier(constants[i], constants_wordlength[i], variables[i], variables[i]._name,\
		 #                         multipliers_wordlength[i], i, RndOff=RndOff, lsb_final=lsb_final) for i in range(N) if constants_wordlength[i] >0]
		multipliers.sort(Multiplier.cmp_lsb)

		# for m in multipliers:
		# 	print m._name,m._cst.integer, m.result.FxPF, m.result.values
		
		# Heuristic for non-exhaustive generation
		# Computation of max_lsb, the maximum difference of lsb between two consecutive multipliers (in the sorted list)
		max_lsb=0
		N=len(multipliers)
		for i in range(N-1):
			max_lsb = max(max_lsb , abs(multipliers[i+1].result.lsb - multipliers[i].result.lsb))
		
		best_osop = None
		h=N
		
		# formatting is the bits cleaning option
		if formatting == True:
			# Computation of fpf_add, ie fpf_final 'plus' delta bits considered for additions
			fpf_add = FPF(wl=fpf_final.wl+delta, msb=fpf_final.msb, lsb=fpf_final.lsb-delta, signed=fpf_final._signed)
			if N ==1:
				best_osop = oSoP(multipliers[0])
				# print best_osop._var_final
			elif N<10:
				best_osop= oSoP_Generator2(multipliers, max_lsb, fpf_add, var_final, formatting=formatting)
			else:
				osop = multipliers[0]
				for m in multipliers[1:]:
					osop = osop.add(m,(False,False,fpf_add))
				best_osop = oSoP(osop, var_final)
				best_osop.Calc_var_result((False,False,fpf_add))
			
		# if formatting == False we use default parameters
		elif formatting == False:
			fpf_add = FPF(wl=adders_wordlength, msb=fpf_final.msb)

			LT=[]
			best_mean = 10000
			# if  7>N >1:
			# 	best_osop = oSoP_Generator2(multipliers, max_lsb, fpf_add, var_final, formatting=formatting)
			if N ==1:
				best_osop = oSoP(multipliers[0])
			else:
				osop = multipliers[0]
				for m in multipliers[1:]:
					osop = osop.add(m,(False,False,fpf_add))
				best_osop = oSoP(osop, var_final)
				best_osop.Calc_var_result((False,False,fpf_add))


			#for L in oSoP_Generator2(multipliers, max_lsb, fpf_add, var_final):
			# 	#if L.height() == ceil(log(N,2)):
			# 	#	return L
			# 	if L._Top._total_error.mean <= best_mean:
			# 		if L._Top._total_error.mean < best_mean:
			# 			LT=[]
			# 		LT.append(L)
			# 		best_mean = L._Top._total_error.mean
			# 		best_osop = L
			# 	else:
			# 		L._Top.kill()

			# h = LT[0].height()
			# for L in LT:
			# 	if L.height() <=h:
			# 		h=L.height()
			# 		best_osop = L
		
		return best_osop



# def oSoP_Generator(list_name_var, list_inter_var, list_cst, list_wl_cst, list_wl_mult, wl_add, fpf_final, alfix = None,plus = None, RndOff = None):

# 	# Un generateur (avec yield) copier-coller depuis tree_thibault.py
# 	# qd j'ai un resultat (une liste de liste), je la passe a list2oSoP qui construit l'oSoP (en appelant recursivement l2oSoP pour chacun des operandes)


# 	# args
# 	N=len(list_cst)
# 	if not isinstance(list_inter_var,list):
# 		list_inter_var = [list_inter_var]*N
# 	if not isinstance(list_wl_cst,list):
# 		list_wl_cst = [list_wl_cst]*N
# 	if not isinstance(list_wl_mult,list):
# 		list_wl_mult = [list_wl_mult]*N
# 	if RndOff and (not isinstance(RndOff,list)):
# 		RndOff = [RndOff]*N
# 	if not isinstance(list_name_var,list):
# 		list_name_var = [list_name_var+repr(i) for i in range(N)]	
# 	Adder.wl_add = wl_add
# 	var_final = Variable(fpf = fpf_final)

# 	# list of results : a result is a couple of couples of couples...
# 	# example : [[1,2],[3,4]] or [[[1,2],3],[4,5]]
# 	results = []


# 	# stack of possibilities to examin : a possibility is list of 
# 	# - a partial result (a list of lists of couples of indexes  )
# 	# - a list of non-yet-used indexes
# 	# example : [ [1,2], 3, 4 ]
# 	stack = [ range(1,N+1)  ]

# 	if RndOff:
# 		stack = [ [ Multiplier(list_cst[i], list_wl_cst[i], list_inter_var[i], list_name_var[i], list_wl_mult[i],i,RndOff[i]) for i in range(N) ] ]
# 	else:
# 		stack = [ [ Multiplier(list_cst[i], list_wl_cst[i], list_inter_var[i], list_name_var[i], list_wl_mult[i],i) for i in range(N) ] ]

# 	stack[0].sort(Multiplier.cmp_lsb)
# 	max_lsb=0
# 	for i in range(N-1):
# 		max_lsb = max(max_lsb,abs(stack[0][i+1].result.lsb-stack[0][i].result.lsb))

# 	delta = int(ceil(log(N,2)))
# 	fpf_add = FxPF(wl=fpf_final.wl+delta, msb=fpf_final.msb, lsb=fpf_final.lsb-delta, signed=fpf_final._signed)


# 	m = len(stack)
# 	while stack:

# 		# get first possibility
# 		osops = stack.pop()

# 		# examin all the possibilities to take two of these osops that satisfies the constraint
# 		# i,j are the two examined osops (with i<j)
# 		for j in range(1,len(osops)):
# 			for i in range(j):
# 				# check if the constraint is ok
# 				if (osops[i] >= osops[0]) and (abs(osops[j].cmp_lsb(osops[i])) <= max_lsb):
# 				#if (osops[i]>=osops[0]):
# 					# re-copy the list
# 					result = osops[:]
# 					# then we can add element i with element j
# 					op_j = result.pop(j)
# 					op_i = result.pop(i)
# 					result.insert( 0, op_i.add(op_j,(alfix,plus,fpf_add)) )
# 					#print len(result)
					
# 					# result is a final result or a partial result according to its length
# 					if len(result)==1:
# 						# add it to the list of possibilities
# 						#we have an oSop
# 						osop = oSoP(result[0], var_final)
# 						osop.Calc_var_result((alfix,plus,fpf_add))
# 						yield osop
# 					else:
# 						# or add this partial result to the stack (some of the osops are not yet used)
# 						stack.append( result)
# 						if len(stack)> m :
# 							m = len(stack)
