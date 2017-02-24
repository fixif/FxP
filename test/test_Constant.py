# coding=utf8

"""
This file contains tests for the Constant class and its methods
"""


__author__ = "Thibault Hilaire, Benoit Lopez"
__copyright__ = "Copyright 2015, FIPOgen Project, LIP6"
__credits__ = ["Thibault Hilaire", "Benoit Lopez"]

__license__ = "CECILL-C"
__version__ = "0.4"
__maintainer__ = "Thibault Hilaire"
__email__ = "thibault.hilaire@lip6.fr"
__status__ = "Beta"


import pytest
from pytest import mark
from mpmath import ldexp, fadd, mpf, almosteq
from random import choice, randint, random
from itertools import chain

from fipogen.FxP import FPF
from fipogen.FxP import Constant


def twoMinusXtwo(signp, p, signq, q, x):
	"""Returns a string and a mp number in form +/-2^p +/- x*2^q"""
	mp = fadd(ldexp(-1 if signp else 1, p), ldexp(-x if signq else x, q), exact=True)
	st = "%s2^%d %s%s*2^%d" % ('-' if signp else '', p, '-' if signq else '+', x.hex(), q)
	return st, mp


def iterSomeNumbers(N, pmax=50, wmax=100):
	"""Generate:
	 - N numbers that are powers of 2 (randomly choose between python floats and mpmath)
	 then
	 - N numbers that are close to some powers of 2 (mpmath or float approx.)
	    (in form +/-2^p +/- x*2^q , with p, q and x random, |p|<=pmax, |p-q|<=wmax and |x|<=1)
	 and finally
	 - N random numbers we can express with at least wmax bits (mpmath or float approx.)
	 Returns the string representation and the float/mp
	 """
	# some powers of 2
	for _ in range(N//10):
		sign = choice((0, 1))
		p = randint(-pmax, pmax)
		# float and mp
		pfloat = -2**p if sign else 2**p
		mp = ldexp(-1 if sign else 1, p)
		usemp = choice((True, False))
		# str
		st = "%s(%s2^%d)" % ('mpf' if usemp else 'float', '-' if sign else '', p)
		yield st, mp if usemp else pfloat

	# some +/-2^p +/- x*2^q , with p, q and x random, |p|<=pmax, |p-q|<=wmax and |x|<=1
	for _ in range(N):
		# build signs, p, q and x
		signp = choice((0, 1))
		signq = choice((0, 1))
		p = randint(-pmax, pmax)
		q = p - randint(0, wmax)
		x = random()
		usemp = choice((True, False))
		st, mp = twoMinusXtwo(signp, p, signq, q, x)
		yield "%s(%s)" % ('mpf' if usemp else 'float',st), mp if usemp else float(mp)

	# some random numbers we can express with at least wmax bits (mpmath or float approx.)
	for _ in range(N):
		st = [ choice("0123456789") for _ in range(randint(int(wmax/2/3.3), int(wmax/3.3)))]
		pos = randint(0,len(st))
		st.insert(pos, ".")
		st = "".join(st)
		yield st, mpf(st)



def iterSomeParticularValues():
	"""Iter some particular values (where we add some trouble, once)
	Returns the str and the values"""

	for p,q,x in [(2,-5,"0x1.e762629cadd10p-2"), (17,-35,"0x1.769706edd66fcp-1"), (-18,-70,"0x1.49c3fb6f2e0b1p-1")]:
		yield twoMinusXtwo(1, p, 0, q, float.fromhex(x))


@mark.parametrize("method", ['','log','Benoit'])
def test_construct(method):
	"""
	Test the Constant constructor
	"""
	c = Constant(value=127, wl=8, signed=False, method=method)
	assert(c.FPF.wml() == (8, 6, -1))
	assert(c.mantissa == 254)

	c = Constant(value=127, wl=8, signed=True, method=method)
	assert(c.FPF.wml() == (8, 7, 0))
	assert(c.mantissa == 127)
	
	c = Constant(value=-127, wl=8, signed=True, method=method)
	assert(c.FPF.wml() == (8, 7, 0))
	assert(c.mantissa == -127)
	
	c = Constant(value=0.36567, wl=8, signed=True, method=method)
	assert(c.FPF.wml() == (8, -1, -8))
	assert(c.mantissa == 94)
	assert(c.approx == 94*2**-8)
	
	with pytest.raises(ValueError):
		Constant(value=-12, wl=12, signed=False, method=method)

	c = Constant(value=127.78, wl=8, signed=False, method=method)
	assert(c.FPF.wml() == (8, 7, 0))
	assert(c.mantissa == 128)
	
	# particular cases
	c = Constant(value=127.78, wl=8, signed=False, method=method)
	assert(c.FPF.wml() == (8, 7, 0))
	assert(c.mantissa == 128)
	c = Constant(value=-128.1, wl=8, signed=True, method=method)
	assert(c.FPF.wml() == (8, 7, 0))
	assert(c.mantissa == -128)
	c = Constant(value=127.7, wl=8, signed=True, method=method)
	assert(c.FPF.wml() == (8, 8, 1))
	assert(c.mantissa == 64)
	
	c = Constant(value=-64.25, wl=8, signed=True, method=method)
	assert(c.FPF.wml() == (8, 6, -1))
	assert(c.mantissa == -128)
	c = Constant(value=-64.3, wl=8, signed=True, method=method)
	assert(c.FPF.wml() == (8, 7, 0))        # !!FIXME: ????(8,6,-1) ?
	assert(c.mantissa == -64)
	c = Constant(value=-64.5, wl=8, signed=True, method=method)     # just in the middle !!
	assert(c.FPF.wml() == (8, 7, 0))
	assert(c.mantissa == -64)
	c = Constant(value=-64.6, wl=8, signed=True, method=method)
	assert(c.FPF.wml() == (8, 7, 0))
	assert(c.mantissa == -65)


	# construct with a given FPF
	with pytest.raises(ValueError):
		Constant(value=258.54, wl=8, fpf=FPF(8, 7, 0))



def checkConstantInit(val, st, signed, wl, fpf):
	"""Check the constant init, by comparing the three methods"""
	methods = ('log','Benoit')
	c = [Constant(val, wl=wl, signed=signed, method=method, fpf=fpf, name=st) for method in methods]

	for cst,me in zip(c,methods):
		print('%s: %s' % (me,cst))


	# check the mantissa range
	for cst in c:
		if signed:
			assert((-2 ** (wl - 1) <= cst.mantissa <= -2 ** (wl - 2)) or (2 ** (wl-2) <= cst.mantissa < 2 ** (wl-1)))
		else:
			assert(2 ** (wl-1) <= cst.mantissa < 2 ** wl)

	# compare the three constants (compare their FPF, mantissa and approx)
	cst = c[0]
	for i in range(1,len(c)):
		assert(cst.FPF == c[i].FPF)
		assert(cst.mantissa == c[i].mantissa)
		assert(cst.approx == c[i].approx)

	# check if |c - c_FxP| < 2 ^(l-1)
	for cst in c:
		assert( almosteq( cst.approx, mpf(val,prec=10*wl), abs_eps=ldexp(1, cst.FPF.lsb-1) ))

	# check lsb is the minimum such as it can be encoded


@mark.parametrize("st_c", chain(iterSomeParticularValues(), iterSomeNumbers(500) ), ids=lambda x: x[0])
def test_alotof_constant_wlfixed(st_c):

	st,c = st_c

	for wl in [8,16, 52, 53, 104, 200, 1065]:
		if c<0:
			checkConstantInit(c, st, signed=True, wl=wl, fpf=None)
		else:
			checkConstantInit(c, st, signed=True, wl=wl, fpf=None)
			checkConstantInit(c, st, signed=False, wl=wl, fpf=None)

