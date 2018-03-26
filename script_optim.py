# -*- coding: utf-8 -*-

from numpy import matrix
import numpy
from Constant import Constant
from math import log, ceil
from scipy.io import loadmat

def coef2msb(M):
	"""Calcule le msb de l'argument M. 
	- si M est un scalaire non nul, retourne le msb de M
	- si M est 0, retourne 'NULL'
	- si M est une liste (ou matrice), retourne la liste (ou matrice) des msb des éléments de M"""
	mM=[]
	if not isinstance(M,list) and not isinstance(M,numpy.ndarray):
	#Si M n'est ni une liste ni un tableau numpy
		if M != 0:
			return Constant(M,16).FPF.msb
		else:
			return "NULL"
	else:
	#Si M est une liste ou un tableau numpy, appels récursifs sur les éléments de M
		for i in range(len(M)):
			mM.append(coef2msb(M[i]))
	return mM

def contraintes(fichier):
	"""A partir d'un fichier .mat, génère le code LaTeX pour l'ensemble des contraintes"""
	# Chargement du fichier
	D = loadmat(fichier)

	# On stocke les éléments du dictionnaire dans des variables
	nt = int(D["l"])
	nx = int(D["n"])
	nu = int(D["m"])
	ny = int(D["p"])
	Z = D["Z"]
	u_m = D["um"]
	u_r = D["ur"]
	dcu = D["dcHu"]
	wcpgu = D["wcpgHu"]
	dce = D["dcHe"]
	wcpge = D["wcpgHe"]

	mZ = coef2msb(Z)

	# Calcul des MSB des variables de sorties (m_var_out) et d'entrées (m_var_in)
	if nu == 1:
		m_var_out = []
		for i in range(nt+nx+ny):
			if abs(u_m*dcu[i] - u_r*wcpgu[i]) > abs(u_m*dcu[i] + u_r*wcpgu[i]):
				diff_out = u_m*dcu[i] - u_r*wcpgu[i]
			else:
				diff_out = u_m*dcu[i] + u_r*wcpgu[i]
			m_var_out.append(Constant(diff_out,16).FPF.msb)
		m_var_in = m_var_out[: (nt+nx)] + [Constant(u_m - u_r,16).FPF.msb]
	else:
		m_var_out = []
		for i in range(nt+nx+ny):
			p = 1
			for j in range(nu):
				if abs(u_m[j]*dcu[i][j] - u_r[j]*wcpgu[i][j]) > abs(u_m[j]*dcu[i][j] + u_r[j]*wcpgu[i][j]):
					diff_out = u_m[j]*dcu[i][j] - u_r[j]*wcpgu[i][j]
				else:
					diff_out = u_m[j]*dcu[i][j] + u_r[j]*wcpgu[i][j]
			p *= diff_out
			m_var_out.append(Constant(p,16).FPF.msb)
		m_var_in = m_var_out[: (nt+nx)] + [Constant(u_m[j] - u_r[j],16).FPF.msb for j in range(nu)]


	# TEX
	wZ = []
	for i in range(1,nt+nx+ny+1):
		if i <= nt :
			L=["w_{%d,%d}^J"%(i,j) for j in range(1,nt+1)] + ["w_{%d,%d}^M"%(i,j) for j in range(1,nx+1)] + ["w_{%d,%d}^N"%(i,j) for j in range(1,nu+1)]
			wZ.append(L)
		elif i <= nt+nx : 
			L=["w_{%d,%d}^K"%(i-nt,j) for j in range(1,nt+1)] + ["w_{%d,%d}^P"%(i-nt,j) for j in range(1,nx+1)] + ["w_{%d,%d}^Q"%(i-nt,j) for j in range(1,nu+1)]
			wZ.append(L)
		else:
			L=["w_{%d,%d}^L"%(i-nt-nx,j) for j in range(1,nt+1)] + ["w_{%d,%d}^R"%(i-nt-nx,j) for j in range(1,nx+1)] + ["w_{%d,%d}^S"%(i-nt-nx,j) for j in range(1,nu+1)]
			wZ.append(L)


	var_out = ["w_{%d}^t"%(i) for i in range(1,nt+1)] + ["w_{%d}^x"%(i) for i in range(1,nx+1)] + ["w_{%d}^y"%(i) for i in range(1,ny+1)]
	var_in = ["w_{%d}^t"%(i) for i in range(1,nt+1)] + ["w_{%d}^x"%(i) for i in range(1,nx+1)] + ["w_{%d}^u"%(i) for i in range(1,nu+1)]


	# Sélection de b :
	print "Voici les msb des variables de sortie :"
	print m_var_out[-ny:]
	print "\nChoisissez les valeurs pour l'erreur"
	b=[]
	for i in range(ny):
		x=float(raw_input("valeur de b_%d:\t"%(i)))
		if int(x)==float(x):
			b.append(float(2**x))
		else:
			b.append(x)
	print b
	

	# Calcul du delta
	d=[]
	for i in range(nt + nx + ny):
		c = 0
		for j in range(nt + nx + nu):
			if Z[i][j] != 0:
				c+=1
		d.append(ceil(log(c,2)))


	# Contraintes de BF
	for i in range(nt + nx + ny):
		for j in range(nt + nx + nu):
			if Z[i][j] != 0:
				print "%s - %s \geq %d\\\\"%(wZ[i][j], var_out[i], m_var_in[j] + mZ[i][j] - m_var_out[i]+ d[i]+1)


	if ny == 1 :
		A = [[abs(dce[i] + wcpge[i]) for i in range(nt+nx+ny)]]
		D = [[abs(dce[i] - wcpge[i]) for i in range(nt+nx+ny)]]
	else:
		A = [[abs(dce[i][j] + wcpge[i][j]) for j in range(nt+nx+ny)] for i in range(ny)]
		D = [[abs(dce[i][j] - wcpge[i][j]) for j in range(nt+nx+ny)] for i in range(ny)]
	

	A2=[]
	for l in A:
		A2.append(list(l))
	D2=[]
	for l in D:
		D2.append(list(l))


	# Calcul des coeff des contraintes d'erreurs avec majoration (A2 et D2)
	bA=[0]*ny
	bD=[0]*ny
	for i in range(ny):
		for j in range(nt+nx+ny):
			if A2[i][j] == max(A2[i][j],D2[i][j]):
				if A2[i][j] != 0:
					bD[i] += float(D2[i][j])/2**(ceil(log(float(A2[i][j])/b[i],2)))
					D2[i][j] = 0
			else:
				if D2[i][j] != 0:
					bA[i] += float(A2[i][j])/2**(ceil(log(float(D2[i][j])/b[i],2)))
					A2[i][j] = 0

	print bA
	print bD

	for i in range(ny):
		for j in range(nt+nx+ny):
			# avec majoration
			A2[i][j] = float(A2[i][j])*2**m_var_out[j] / (b[i]-bA[i])
			D2[i][j] = float(D2[i][j])*2**m_var_out[j] / (b[i]-bD[i])
			# sans majoration
			A[i][j] = float(A[i][j])*2**m_var_out[j] / b[i]
			D[i][j] = float(D[i][j])*2**m_var_out[j] / b[i]


	print "\n\nContraintes sans majoration\n"

	for i in range(ny):
		cA = ""
		cD = ""
		for j in range(nt + nx + ny):
			if (A[i][j] != 0) :
				cA += "\\frac{%g}{2^{%s}}"%(A[i][j],var_out[j])
				if (j != nt+nx+ny - 1) and ([A[i][k] for k in range(j+1, nt + nx + ny) if A[i][k] != 0] != []):
					cA += " + "
			if (D[i][j] != 0) :
				cD += "\\frac{%g}{2^{%s}}"%(D[i][j],var_out[j])
				if (j != nt+nx+ny - 1) and ([D[i][k] for k in range(j+1, nt + nx + ny) if D[i][k] != 0] != []):
					cD += " + "
		cA += "\leq 1\\\\"
		cD += "\leq 1\\\\"
		print cA+"\n"
		print cD+"\n"


	print "\n\nContraintes avec majoration\n"

	for i in range(ny):
		cA = ""
		cD = ""
		for j in range(nt + nx + ny):
			if (A2[i][j] != 0) :
				cA += "\\frac{%g}{2^{%s}}"%(A2[i][j],var_out[j])
				if (j != nt+nx+ny - 1) and ([A2[i][k] for k in range(j+1, nt + nx + ny) if A2[i][k] != 0] != []):
					cA += " + "
			if (D2[i][j] != 0) :
				cD += "\\frac{%g}{2^{%s}}"%(D2[i][j],var_out[j])
				if (j != nt+nx+ny - 1) and ([D2[i][k] for k in range(j+1, nt + nx + ny) if D2[i][k] != 0] != []):
					cD += " + "
		cA += "\leq 1\\\\"
		cD += "\leq 1\\\\"
		print cA+"\n"
		print cD+"\n"


def contraintes_AMPL(fichier):
	"""A partir d'un fichier .mat, génère le code AMPL pour l'ensemble des contraintes"""
	D = loadmat(fichier)
	nt = int(D["l"])
	nx = int(D["n"])
	nu = int(D["m"])
	ny = int(D["p"])
	Z = D["Z"]
	u_m = D["um"]
	u_r = D["ur"]
	dcu = D["dcHu"]
	wcpgu = D["wcpgHu"][0]
	dce = D["dcHe"][0]
	wcpge = D["wcpgHe"]

	mZ = coef2msb(Z)

	# Calcul des MSB des variables de sorties (m_var_out) et d'entrées (m_var_in)
	if nu == 1:
		m_var_out = []
		for i in range(nt+nx+ny):
			# calcul de la plus grande valeur représentable dans l'intervalle
			if abs(u_m*dcu[i] - u_r*wcpgu[i]) > abs(u_m*dcu[i] + u_r*wcpgu[i]):
				diff_out = u_m*dcu[i] - u_r*wcpgu[i]
			else:
				diff_out = u_m*dcu[i] + u_r*wcpgu[i]
			# calcul du msb de cette plus grance valeur
			m_var_out.append(coef2msb(diff_out))
		m_var_in = m_var_out[: (nt+nx)] + [coef2msb(u_m - u_r)]
	else:
		m_var_out = []
		for i in range(nt+nx+ny):
			p = 1
			for j in range(nu):
				if abs(u_m[j][0]*dcu[i][j] - u_r[j][0]*wcpgu[i][j]) > abs(u_m[j][0]*dcu[i][j] + u_r[j][0]*wcpgu[i][j]):
					diff_out = u_m[j][0]*dcu[i][j] - u_r[j][0]*wcpgu[i][j]
				else:
					diff_out = u_m[j][0]*dcu[i][j] + u_r[j][0]*wcpgu[i][j]
			p *= diff_out
			m_var_out.append(coef2msb(p))
		m_var_in = m_var_out[: (nt+nx)] + [coef2msb(u_m[j][0] - u_r[j][0]) for j in range(nu)]


		# Sélection de b :
	#print "Voici les msb des variables de sortie :"
	# print m_var_out[-ny:]
	#print "\nChoisissez les valeurs pour l'erreur"
	# b=[]
	# for i in range(ny):
	# 	x=float(raw_input("valeur de b_%d:\t"%(i)))
	# 	if int(x)==float(x):
	# 		b.append(float(2**x))
	# 	else:
	# 		b.append(x)
	# print b

	# je choisis mes bornes sur l'erreur pour avoir 8 bits de juste sur le résultat final
	b=[]
	for i in m_var_out[-ny:]:
		b.append(-3)


	# calcul du delta
	d=[]
	for i in range(nt + nx + ny):
		c = 0
		for j in range(nt + nx + nu):
			if Z[i][j] != 0:
				c+=1
		d.append(int(ceil(log(c,2))))


	# mat_cst_BF = []

	# for i in range(nt + nx + ny):
	# 	L=[]
	# 	for j in range(nt + nx + nu):
	# 		L.append(m_var_in[j] + mZ[i][j] - m_var_out[i]+ d[i]+1)
	# 	mat_cst_BF.append(L)


	if ny == 1 :
		A = [[abs(dce[i] + wcpge[i]) for i in range(nt+nx+ny)]]
		D = [[abs(dce[i] - wcpge[i]) for i in range(nt+nx+ny)]]
	else:
		A = [[abs(dce[i][j] + wcpge[i][j]) for j in range(nt+nx+ny)] for i in range(ny)]
		D = [[abs(dce[i][j] - wcpge[i][j]) for j in range(nt+nx+ny)] for i in range(ny)]
	

	print m_var_out
	for i in range(ny):
		for j in range(nt+nx+ny):
			# sans majoration
			A[i][j] = float(A[i][j])*2**(m_var_out[j]+1) / b[i]
			D[i][j] = float(D[i][j])*2**(m_var_out[j]+1) / b[i]

	# MaxAD = []
	# for i in range(ny):
	# 	L=[]
	# 	for j in range(nt+nx+ny):
	# 		L.append(max(A[i][j],D[i][j]))
	# 	MaxAD.append(L)

	# MaxA = []
	# MaxD = []
	# for i in range(ny):
	# 	LA=[]
	# 	LD=[]
	# 	for j in range(nt+nx+ny):
	# 		if A[i][j] == max(A[i][j],D[i][j]):
	# 			LA.append(max(A[i][j],D[i][j]))
	# 			LD.append(0)
	# 		else:
	# 			LD.append(max(A[i][j],D[i][j]))
	# 			LA.append(0)
	# 	MaxA.append(LA)
	# 	MaxD.append(LD)


	
	txt_i = "param N := %d;\n"%(nt+nx)
	txt_i += "param M := %d;\n"%(ny)
	txt_i += "param Q := %d;\n\n"%(2*ny)
	txt_i += "#--- Objective function\n\n"
	txt_i += "param c := \n"
	for j in range(nt+nx):
		txt_i += "\t%d 1\n"%(j+1)
	txt_i += ";\n\nparam d := \n"
	for j in range(ny):
		txt_i += "\t%d 1\n"%(j+1)

	k=97
	txt_i += ";\n\n#--- Constraint %d\nparam coefx :"%(k-96)
	for j in range(nt+nx):
		txt_i += " %d"%(j+1)
	txt_i += " :="
	for i in range(ny):
		txt_i += "\n\t%d"%(i*2+1)
		for j in range(nt+nx):
			txt_i += " %lf"%(A[i][j])
		txt_i += "\n\t%d"%(i*2+2)
		for j in range(nt+nx):
			txt_i += " %lf"%(D[i][j])
	txt_i += ";\n\n"

	txt_i += "param coefy :"
	for j in range(ny):
		txt_i += " %d"%(j+1)
	txt_i += " :="
	for i in range(ny):
		txt_i += "\n\t%d"%(i*2+1)
		for j in range(ny):
			txt_i += " %lf"%(A[i][j+(nt+nx)])
		txt_i += "\n\t%d"%(i*2+2)
		for j in range(ny):
			txt_i += " %lf"%(D[i][j+(nt+nx)])
	txt_i += ";\n\n"


	
	# for i in range(ny):
	# 	txt_i += "#--- Constraint %d\nparam coef%cx :="%(k-96,chr(k))
	# 	for j in range(nt+nx):
	# 		txt_i += "\n\t%d %g"%(j+1,A[i][j])
	# 	txt_i += ";\n\n"
	# 	txt_i += "param coef%cy :="%(chr(k))
	# 	for j in range(ny):
	# 		txt_i += "\n\t%d %g"%(j+1,A[i][j+(nt+nx)])
	# 	txt_i += ";\n\n"
	# 	k += 1

	# for i in range(ny):
	# 	txt_i += "#--- Constraint %d\nparam coef%cx :="%(k-96,chr(k))
	# 	for j in range(nt+nx):
	# 		txt_i += "\n\t%d %g"%(j+1,D[i][j])
	# 	txt_i += ";\n\n"
	# 	txt_i += "param coef%cy :="%(chr(k))
	# 	for j in range(ny):
	# 		txt_i += "\n\t%d %g"%(j+1,D[i][j+(nt+nx)])
	# 	txt_i += ";\n\n"
	# 	k += 1
		
	# print txt_i
	# print "\n\n"

	# txt_i = "param N := %d;\n"%(nt+nx)
	# txt_i += "param M := %d;\n\n"%(ny)

	# k=97
	# for i in range(ny):
	# 	txt_i += "#--- Constraint %d\nparam coef%cx :="%(k-96,chr(k))
	# 	for j in range(nt+nx):
	# 		txt_i += "\n\t%d %g"%(j+1,MaxAD[i][j])
	# 	txt_i += ";\n\n"
	# 	txt_i += "param coef%cy :="%(chr(k))
	# 	for j in range(ny):
	# 		txt_i += "\n\t%d %g"%(j+1,MaxAD[i][j+(nt+nx)])
	# 	txt_i += ";\n\n"
	# 	k += 1
		
	# print txt_i
	# print "\n\n"

	# txt_i = "param N := %d;\n"%(nt+nx)
	# txt_i += "param M := %d;\n\n"%(ny)

	# k=97
	# for i in range(ny):
	# 	txt_i += "#--- Constraint %d\nparam coef%cx :="%(k-96,chr(k))
	# 	for j in range(nt+nx):
	# 		txt_i += "\n\t%d %g"%(j+1,MaxA[i][j])
	# 	txt_i += ";\n\n"
	# 	txt_i += "param coef%cy :="%(chr(k))
	# 	for j in range(ny):
	# 		txt_i += "\n\t%d %g"%(j+1,MaxA[i][j+(nt+nx)])
	# 	txt_i += ";\n\n"
	# 	k += 1

	# for i in range(ny):
	# 	txt_i += "#--- Constraint %d\nparam coef%cx :="%(k-96,chr(k))
	# 	for j in range(nt+nx):
	# 		txt_i += "\n\t%d %g"%(j+1,MaxD[i][j])
	# 	txt_i += ";\n\n"
	# 	txt_i += "param coef%cy :="%(chr(k))
	# 	for j in range(ny):
	# 		txt_i += "\n\t%d %g"%(j+1,MaxD[i][j+(nt+nx)])
	# 	txt_i += ";\n\n"
	# 	k += 1

	print txt_i





