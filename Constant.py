# coding=utf8

"""
The Constant class allows to represent constant coefficients in fixed-point arithmetic
"""

__author__ = "Thibault Hilaire, Benoit Lopez"
__copyright__ = "Copyright 2015, FIPOgen Project, LIP6"
__credits__ = ["Thibault Hilaire", "Benoit Lopez"]

__license__ = "CECILL-C"
__version__ = "0.4"
__maintainer__ = "Thibault Hilaire"
__email__ = "thibault.hilaire@lip6.fr"
__status__ = "Beta"

from fipogen.FxP import FPF
from math import log, floor, ceil


class Constant(object):
	"""Constant class to store (non-null) constant coefficient in fixed-point arithmetic
	
	Attributes:
		_value: real value of the constant (in fact, floating-point value for the moment... Use MPFI in the future)
		_FPF: Fixed-Point Format used to represent the constant
		_mantissa: Integer value used to approximate the constant in the given FPF
	"""

	def __init__(self, value, wl=None, signed=True, fpf=None):
		"""Constructs a constant object, from a real value (now a float/double... MPFI could be used in the future), encoded with wl bits. 
		Args:
			value: the real value of the constant
			wl: word-length
			signed: True if signed fixed-point arithmetic is used, False if unsigned arithmetic
			fpf: Fixed-Point Format
		Raises:
			ValueError if the parameters' values are not coherent
		"""

		if ((fpf is None) and (wl is None)) or ((fpf is not None) and (wl is not None) and (fpf.wl != wl)):
			raise ValueError("Bad combination of arguments")
		elif fpf is not None:
			wl = fpf.wl

		self._value = value

		# check for non-sense values
		if signed is False and value < 0:
			raise ValueError("Unsigned FPF with negative constant !!")
		if value == 0:
			raise ValueError("zero cannot be stored in a Constant !!")
		# if fpf and (fpf.wl != wl):
		# 	raise ValueError( "Conflict between wordlengths !!")
		if fpf and (fpf.signed != signed):
			raise ValueError("Conflict between signs !!")

		# unsiged case
		if signed is False:
			msb = fpf.msb if fpf else int(floor(log(value, 2)))
			self._mantissa = int(round(value * 2 ** (wl - msb - 1)))
			# check for particular case (when the quantized constant overpass the limit whereas the constant doesN'T)
			if self._mantissa == 2 ** wl:
				# like for the case 127.8 on 8 bits unsigned...
				msb += 1
				# self._integer = int ( round( value * 2**(wl-msb-1)) )
				self._mantissa = 2 ** (wl - 1)

		# signed case
		else:
			if fpf:
				# compute msb
				msb = fpf.msb
				# compute N
				self._mantissa = int(round(value * 2 ** (wl - msb - 1)))
			else:
				# compute msb
				msb = (int(floor(log(abs(value), 2))) + 1) if value > 0 else (int(ceil(log(abs(value), 2))))
				# compute N
				self._mantissa = int(round(value * 2 ** (wl - msb - 1)))

				# check for particular case (when the value overpass the limit BUT the quantized value doesN'T, or the opposite)
				if self._mantissa == 2 ** (wl - 1):
					# like 127.8 on 8 bits
					msb += 1
					self._mantissa = 2 ** (wl - 2)
				elif self._mantissa == -2 ** (wl - 2):
					# like -128.1 on 8 bits
					msb -= 1
					self._mantissa = -2 ** (wl - 1)

		# associated FPF
		if fpf and ((not signed and not (0 <= self._mantissa < 2 ** wl))
		            or (signed and not (-2 ** (wl - 1) <= self._mantissa < 2 ** (wl - 1)))):
			raise ValueError(" given FPF cannot represent value")
		if self._mantissa == 0:
			raise ValueError("The FPF is not enough to represent the constant without underflow !")
		self._FPF = FPF(wl=wl, msb=msb, signed=signed)

	@property
	def mantissa(self):
		"""Returns the integer representing the constant"""
		return self._mantissa

	@property
	def FPF(self):
		"""Returns the fixed-point format of the constant"""
		return self._FPF

	@property
	def value(self):
		"""Returns the value"""
		return self._value

	@property
	def approx(self):
		"""Return the approximation of the constant with the chosen fixed-point format"""
		return self._mantissa * 2 ** self._FPF.lsb
