# coding=utf8

"""
This file contains tests for the FPF class and its methods
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
from FxP import FPF
from random import randint, choice
from pytest import mark


def test_construct():
	"""Unit test for the FPF constructor"""
	# construct FPF with less than 2 args
	with pytest.raises(ValueError):
		FPF(16)
	with pytest.raises(ValueError):
		FPF(msb=12)
	with pytest.raises(ValueError):
		FPF(lsb=-6)

	# construct with wrong wl
	with pytest.raises(ValueError):
		FPF(wl=-12, msb=6)
	with pytest.raises(ValueError):
		FPF(wl=1, msb=6, signed=True)


	# construct FPF with only wl and (lsb or msb)
	f = FPF(16, lsb=-12)
	assert(f.wml() == (16, 3, -12))
	f = FPF(16, msb=3)
	assert(f.wml() == (16, 3, -12))
	f = FPF(16, msb=0)
	assert(f.wml() == (16, 0, -15))
	with pytest.raises(ValueError):
		FPF(16, 12, -5)
	
	# construct form string
	f = FPF(formatStr="Q8.12")
	assert(f.wml() == (20, 7, -12))
	f = FPF(formatStr="sQ4.3")
	assert(f.wml() == (7, 3, -3))
	f = FPF(formatStr="uQ4.3")
	assert(f.wml() == (7, 3, -3))
	f = FPF(formatStr="(8,-12)")
	assert(f.wml() == (21, 8, -12))
	f = FPF(formatStr="u(8,-12)")
	assert(f.signed is False)
	assert(f.wml() == (21, 8, -12))
	with pytest.raises(ValueError):
		FPF(formatStr="totoQ6.8")
		
	f = FPF(msb=7, lsb=0, signed=True)
	assert(f.minmax() == (-128, 127))
	f = FPF(msb=7, lsb=0, signed=False)
	assert(f.minmax() == (0, 255))


# def test_shift():
# 	""" Test the shifts
# 	"""
# 	# TODO: complete the tests
# 	f = FPF(16, 3, -12)
# 	f.shift(2)
# 	assert(f.wml() == (16, 5, -10))




# def test_approx():
# 	"""Test the approx method"""
# 	# TODO: do it over a large number of values
# 	F = FPF(msb=7, lsb=0)
# 	assert(F.approx(25) == 25)
# 	assert(F.approx(25.001) == 25)
# 	assert(F.approx(25.26789) == 25)


def iterSomeFPF(N):
	for _ in range(N):
		w = randint(2,30)
		m = randint(-30,30)
		s = choice([True,False])
		yield FPF(wl=w, msb=m, signed=s)



#y_origin=0, colors=None,  binary_point=False, label='no', notation='mlsb', numeric=False, intfrac=False, power2=False, hatches=None, bits=None, x_shift=0, drawMissing=False, **_):
@mark.parametrize("y_origin",[randint(-5,5) for _ in range(3)])
@mark.parametrize("binary_point", [True, False])
@mark.parametrize("label", ['left', 'right', 'above', 'below', 'no'])
@mark.parametrize("notation", ["mlsb", "ifwl"])
@mark.parametrize("numeric", [True,False])
@mark.parametrize("intfrac", [True,False])
@mark.parametrize("power2", [True,False])
@mark.parametrize("fpf", iterSomeFPF(50) )
def test_LaTeX(fpf, y_origin, binary_point, label, notation, numeric, intfrac, power2):
	fpf.LaTeX(y_origin=y_origin, binary_point=binary_point, label=label, notation=notation, numeric=numeric, intfrac=intfrac, power2=power2)