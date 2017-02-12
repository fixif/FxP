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

from fipogen.FxP.FPF import FPF

from mpmath import mpf, workprec, log, floor, ceil


class Constant(object):
	"""Constant class to store (non-null) constant coefficient in fixed-point arithmetic
	
	Attributes:
		_value: real value of the constant, given at construction (in fact, it could be a float, a mpf object or even a string)
		_FPF: Fixed-Point Format used to represent the constant
		_mantissa: (Long) mantissa of the constant (integer used to approximate the constant in the given FPF)

	mpmath package is used to convert the value ("0.1" for example) and do the log2 computations
	"""

	def __init__(self, value, wl=None, signed=None, fpf=None):
		"""Constructs a constant object, from a real value (something that mpmath can handle, so a float or a string).
		 It could be build with wl bits (and signedness) OR (exclusive) with the given fpf
		Parameters:
		- value: (float, string or mpf) the real value of the constant
		- wl: (positive integer) word-length
		- signed: (boolean) True if signed fixed-point arithmetic is used, False if unsigned arithmetic
		- fpf: (FPF) Fixed-Point Format
		Raises:
			ValueError if the parameters' values are not coherent
		"""
		# combination of arguments (wl AND signed) XOR fpf
		if wl is None and signed is None and fpf is not None:
			wl = fpf.wl
			signed = fpf.signed
		elif not(wl is not None and signed is not None and fpf is None):
			raise ValueError("Bad combination of arguments")
		if wl <= 1:
			raise ValueError("The word-length should be at least equal to 2")

		# store the exact value given and it's approximated value with 2*wl bits in mpmath
		self._value = value
		mpvalue = mpf(value, prec=max(53, 2*wl))       # TODO: prec = wl+1 should be enough ??

		# check for non-sense values
		if signed is False and mpvalue < 0:
			raise ValueError("Unsigned FPF with negative constant !!")

		# treat null constant
		if mpvalue == 0:
			self._mantissa = 0L
			self._value = 0
			self._fpf = FPF(wl=wl, lsb=0)        # arbitrary choose lsb=0
			# raise ValueError("zero cannot be stored in a Constant !!")
			return

		with workprec(max(53, 2*wl)):       # with at least 53 bits, or 2*wl bits

			# compute MSB
			if fpf:
				msb = fpf.msb
			elif mpvalue>0:
				msb = int(floor(log(mpvalue, 2))) + (1 if signed else 0)
			else:
				msb = int(ceil(log(-mpvalue, 2)))

			# compute mantissa
			self._mantissa = long(round(mpvalue * 2 ** (wl - msb - 1)))

			# check for particular case (when the quantized constant overpass the limit whereas the constant doesN'T)
			if self._mantissa == 2 ** (wl - (1 if signed else 0)):
				# like for the case 127.8 on 8 bits unsigned...
				msb += 1
				self._mantissa = 2 ** (wl - (2 if signed else 1))
			elif self._mantissa == -2 ** (wl - 2):
				# like -128.1 on 8 bits
				msb -= 1
				self._mantissa = -2 ** (wl - 1)

		# check if the mantissa is valid when a fpf is given
		if (not signed and not (0 <= self._mantissa < 2 ** wl)
		    or (signed and not (-2 ** (wl - 1) <= self._mantissa < 2 ** (wl - 1)))):
			raise ValueError("given FPF cannot represent value")
		if self._mantissa == 0:
			# TODO: add an option to return a null constant rather raise an exception
			raise ValueError("The FPF is not enough to represent the constant without underflow !")

		# associated FPF
		self._FPF = FPF(wl=wl, msb=msb, signed=signed)


	@property
	def mantissa(self):
		"""Returns the mantissa (the integer representing the constant)"""
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
		# TODO: return mpmath ?
		return self._mantissa * 2**self._FPF.lsb
