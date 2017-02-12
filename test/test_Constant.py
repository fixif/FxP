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
from fipogen.FxP import FPF
from fipogen.FxP import Constant


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

