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
from fipogen.FxP import FPF


def test_construct():
	"""Unit test for the FPF constructor"""
	# construct FPF with less than 2 args
	with pytest.raises(ValueError):
		f = FPF(16)
	with pytest.raises(ValueError):
		f = FPF(msb=12)
	with pytest.raises(ValueError):
		f = FPF(lsb=-6)		
	
	# construct FPF with only wl and (lsb or msb)
	f = FPF(16, lsb=-12)
	assert(f.wml() == (16, 3, -12))
	f = FPF(16, msb=3)
	assert(f.wml() == (16, 3, -12))
	f = FPF(16, msb=0)
	assert(f.wml() == (16, 0, -15))
	with pytest.raises(ValueError):
		f = FPF(16, 12, -5)
	
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
		f = FPF(formatStr="totoQ6.8")
		
	f = FPF(msb=7, lsb=0, signed=True)
	assert(f.minmax() == (-128, 127))
	f = FPF(msb=7, lsb=0, signed=False)
	assert(f.minmax() == (0, 255))


def test_shift():
	""" Test the shifts
	"""
	# TODO: complete the tests
	f = FPF(16, 3, -12)
	f.shift(2)
	assert(f.wml() == (16, 5, -10))

	
def test_approx():
	"""Test the approx method"""
	# TODO: do it over a large number of values
	F = FPF(16, 8)
	assert(F.approx(25) == 25)
	assert(F.approx(25.001) == 25)
	assert(F.approx(25.26789) == 25.265625)

