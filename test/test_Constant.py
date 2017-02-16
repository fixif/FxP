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
from mpmath import ldexp, fadd, mpf
from random import choice, randint, random
from fipogen.FxP import FPF
from fipogen.FxP import Constant


def iterSomeNumbers(N, pmax=50, wmax=100):
	"""Generate:
	 - N numbers that are powers of 2 (randomly choose between python floats and mpmath)
	 then
	 - N numbers that are close to some powers of 2 (mpmath or float approx.)
	    (in form +/-2^p +/- x*2^q , with p, q and x random, |p|<=pmax, |p-q|<=wmax and |x|<=1)
	 and finally
	 - N random numbers we can express with at least wmax bits (mpmath or float approx.)
	 """
	# some powers of 2
	for _ in range(N):
		sign = choice((0, 1))
		p = randint(-pmax, pmax)
		# float and mp
		pfloat = -2**p if sign else 2**p
		mp = ldexp(-1 if sign else 1, p)
		yield choice((pfloat, mp))

	for _ in range(N):
		# build signs, p, q and x
		signp = choice((0, 1))
		signq = choice((0, 1))
		p = randint(-pmax, pmax)
		q = p - randint(0, wmax)
		x = random()
		# mp
		mp = fadd(ldexp(-1 if signp else 1, p), ldexp(-x if signq else x, q))
		yield choice((mp,float(mp)))





def test_construct():
	"""
	Test the Constant constructor
	"""
	c = Constant(value=127, wl=8, signed=False)
	assert(c.FPF.wml() == (8, 6, -1))
	assert(c.mantissa == 254)

	c = Constant(value=127, wl=8, signed=True)
	assert(c.FPF.wml() == (8, 7, 0))
	assert(c.mantissa == 127)
	
	c = Constant(value=-127, wl=8, signed=True)
	assert(c.FPF.wml() == (8, 7, 0))
	assert(c.mantissa == -127)
	
	c = Constant(value=0.36567, wl=8, signed=True)
	assert(c.FPF.wml() == (8, -1, -8))
	assert(c.mantissa == 94)
	assert(c.approx == 94*2**-8)
	
	with pytest.raises(ValueError):
		Constant(value=-12, wl=12, signed=False)

	c = Constant(value=127.78, wl=8, signed=False)
	assert(c.FPF.wml() == (8, 7, 0))
	assert(c.mantissa == 128)
	
	# particular cases
	c = Constant(value=127.78, wl=8, signed=False)
	assert(c.FPF.wml() == (8, 7, 0))
	assert(c.mantissa == 128)
	c = Constant(value=-128.1, wl=8, signed=True)
	assert(c.FPF.wml() == (8, 7, 0))
	assert(c.mantissa == -128)
	c = Constant(value=127.7, wl=8, signed=True)
	assert(c.FPF.wml() == (8, 8, 1))
	assert(c.mantissa == 64)
	
	c = Constant(value=-64.25, wl=8, signed=True)
	assert(c.FPF.wml() == (8, 6, -1))
	assert(c.mantissa == -128)
	c = Constant(value=-64.3, wl=8, signed=True)
	assert(c.FPF.wml() == (8, 6, -1))
	assert(c.mantissa == -128)
	c = Constant(value=-64.5, wl=8, signed=True)
	assert(c.FPF.wml() == (8, 7, 0))
	assert(c.mantissa == -65)
	
	# construct with a given FPF
	with pytest.raises(ValueError):
		Constant(value=258.54, wl=8, fpf=FPF(8, 7, 0))



@mark.parametrize("c", iterSomeNumbers(50), ids=lambda x: str(x))
def test_values(c, wl=8):

	cB = Constant(c, wl=wl, signed=True, method='Benoit')
	cL = Constant(c, wl=wl, signed=True, method='log')

	assert(cB.FPF == cL.FPF)
	assert(cB.mantissa == cL.mantissa)
	assert(cB.approx == cL.approx)