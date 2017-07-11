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
from mpmath import mpf, workprec, log, floor, ceil, ldexp, frexp, nint, fadd, fsub, mpmathify


class Constant:
	"""Constant class to store a (non-null) constant in fixed-point arithmetic
	
	Attributes:
		_value: real value of the constant, given at construction (in fact, it could be a float, a mpf object or even a string)
		_FPF: Fixed-Point Format used to represent the constant
		_mantissa:  mantissa of the constant (integer used to approximate the constant in the given FPF)

	mpmath package is used to convert the value ("0.1" for example) and do the log2 computations
	"""

	def __init__(self, value, wl=None, signed=None, fpf=None, method='float', name=None):
		"""Constructs a constant object, from a real value (something that mpmath can handle, so a float or a string).
		 It could be build with wl bits (and signedness) OR (exclusive) with the given fpf
		Parameters:
		- value: (float or mpf) the real value of the constant
		- wl: (positive integer) word-length
		- signed: (boolean) True if signed fixed-point arithmetic is used, False if unsigned arithmetic
		- fpf: (FPF) Fixed-Point Format
		- method: (string) should be
				'float' (default) for using the mantissa from floating-point conversion (using mpmath if it's a string)
				'Benoit' for using Benoit's method (see "Reliable Implementation of Linear Filters with Fixed-Point Arithmetic", Hilaire and Lopez, 2013)
				'log' using the complete logarithm-based formula
				-> Of course, the 3 methods returns the same results
		Raises:
			ValueError if the parameters' values are not coherent
		"""
		# combination of arguments (wl AND signed) XOR fpf
		if wl is not None and fpf is not None:
			raise ValueError("Bad combination of arguments: cannot give a word-length and a FPF in the same time")
		if wl is None and fpf is None:
			raise ValueError("Bad combination of arguments: no wordlength or FPF given")
		if wl is not None and wl < 2:
			raise ValueError("Constant: The word-length should be at least equal to 2")
		if signed is None and fpf is None:
			signed = True
		# store name
		if name:
			self._name = name
		else:
			self._name = str(value)

		# store the exact value given (string, float or mpf) and it's mp math conversion (losslessly)
		self._value = value
		mpvalue = mpmathify(value)

		# check for non-sense values
		if signed is False and mpvalue < 0:
			raise ValueError("Unsigned FPF with negative constant !!")

		# treat null constant
		if mpvalue == 0:
			self._mantissa = 0
			self._value = 0
			self._FPF = FPF(wl=wl, lsb=0)        # arbitrary choose lsb=0
			# raise ValueError("zero cannot be stored in a Constant !!")
			return

		# conversion to a given FPF
		if fpf is not None:
			# do the conversion
			self._FPF = fpf
			self._mantissa = nint(ldexp(mpvalue, -fpf.lsb))
			self._value = ldexp( self._mantissa, fpf.lsb)
			# check if mantissa is ok
			if signed:
				if not -2**(fpf.wl-1) <= self._mantissa <= (2**(fpf.wl-1) - 1):
					raise ValueError("The constant cannot be converted to the FPF %s", fpf)
			else:
				if not signed and not 0 <= self._mantissa <= (2**fpf.wl-1):
					raise ValueError("The constant cannot be converted to the FPF %s", fpf)
			# check underflow
			#TODO: add option to allow underflow (sometimes useful)
			if self._mantissa == 0:
				raise ValueError("Underflow during the conversion of the constant!")
			return

		# Otherwise, perform the best w-bit conversion (with different methods)
		if method == 'Benoit':
			# Benoit's method (ie log2 + check for special cases)
			# see "Reliable Implementation of Linear Filters with Fixed-Point Arithmetic", Hilaire and Lopez, 2013
			with workprec(20*wl):       # "enough bits"
				# compute MSB
				# if fpf:
				# 	msb = fpf.msb
				if mpvalue > 0:
					msb = int(floor(log(mpvalue, 2))) + (1 if signed else 0)
				else:
					msb = int(ceil(log(-mpvalue, 2)))

				# compute mantissa
				self._mantissa = int(nint(ldexp(mpvalue, (wl - msb - 1))))      # round-to-nearest even

				# check for particular case (when the quantized constant overpass the limit whereas the constant doesN'T)
				if self._mantissa == 2 ** (wl - (1 if signed else 0)):
					# like for the case 127.8 on 8 bits unsigned...
					msb += 1
					self._mantissa = 2 ** (wl - (2 if signed else 1))
				elif self._mantissa == -2 ** (wl - 2):
					# like -128.1 on 8 bits
					msb -= 1
					self._mantissa = -2 ** (wl - 1)


		elif method == 'log':
			# log2-based method (only based on logarithm base 2, with exact mp arithmetic)
			# that takes care of two's complement asymmetry
			with workprec(20*wl+1):        # enough ??
				# set the msb
				if mpvalue > 0:
					corr = fsub(1, ldexp(1, -wl + (0 if signed else -1)), exact=True)
					msb = int(floor(log(mpvalue/corr, 2))) + (1 if signed else 0)
				else:
					corr = fadd(1, ldexp(1, -wl+1), exact=True)
					msb = int(ceil(log(-mpvalue/corr, 2)))
				# set the lsb and the mantissa
				lsb = msb + 1 - wl
				self._mantissa = max(int(nint(ldexp(mpvalue, -lsb))), -2**(wl-1))             # round-to-nearest even

		elif method == 'threshold':
			# compute the minimum wordlength where the constant is not a special case (boundaries)
			with workprec(20*wl):       # enough?
				# compute wmin
				if mpvalue > 0:
					fr = mpvalue/2**floor(log(mpvalue, 2))       # fr = 2**frac(log(mpvalue, 2))
					if fr<2:
						wmin = int(floor(-log(2 - fr, 2))) + (2 if signed else 1)
					else:
						# should not happen when fr is computed with infinite precision... here, it happens
						wmin = mpf('+inf')
				else:
					fr = -mpvalue/2**ceil(log(-mpvalue, 2))
					wmin = int(floor(-log(2*fr - 1, 2)) + 2)
				# compute msb
				if mpvalue > 0:
					msb = int(floor(log(mpvalue, 2))) + (1 if signed else 0) + (1 if wl < wmin else 0)
				else:
					msb = int(ceil(log(-mpvalue, 2))) - (1 if wl < wmin else 0)
				# compute lsb and mantissa
				lsb = msb + 1 - wl
				self._mantissa = max(int(nint(ldexp(mpvalue, -lsb))), -2**(wl-1))             # round-to-nearest even


		else:
			# default method
			# since the value is already transformed in floating-point (mantissa + exponent) with mpmath
			# we can use that mantissa and exponent (be careful of the two's complement asymmetry, -2^p is ok with msb=p)
			with workprec(20*wl):

				# floating-point with the right word-length
				fl = mpf(value, prec=wl - (1 if signed else 0))
				# since mpmath do not have the integral significant (with MSB=1), we take the normalized significant
				# and build the mantissa (M) and exponent (e)
				m, ep = frexp(fl)
				M = ldexp(m, wl - (1 if signed else 0))
				e = ep - wl + (1 if signed else 0)
				# FxP mantissa, msb and lsb
				self._mantissa = int(M)
				lsb = e
				msb = wl + lsb - 1
				if self._mantissa == -2**(wl-2):
					lsb -= 1
					msb -= 1
					self._mantissa = -2**(wl-1)

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
		return ldexp(self._mantissa,  self._FPF.lsb)

	def __str__(self):
		return "<Constant(%s): %d*2^%d>" % (self._name, self._mantissa, self._FPF.lsb)

	def __repr__(self):
		return str(self)

