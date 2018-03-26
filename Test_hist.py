from Generated.Code.code import *
from matplotlib import pylab
import numpy as np
from random import randint,choice

L_err=[]

for i in range(1000000):
	T = [float(choice([randint(-2**15,-2**14-1),randint(2**14,2**15-1)])) for i in range(9)]
	F = SoP_float(T)
	acF = SoP_ac_fixed(T)
	L_err.append(F-acF)

	
print(np.mean(L_err))
print(np.var(L_err))

n,bins,patches=pylab.hist(L_err,100,normed=1,histtype='step')

pylab.axis([-max(bins), max(bins)*1.1, 0, max(n)])

pylab.show()