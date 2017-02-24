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

from mpmath import mpf, workprec, log, floor, ceil, ldexp, frexp, nint, extraprec, frac, fadd, fsub


class Constant(object):
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
		- value: (float, string or mpf) the real value of the constant
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
		if wl is None and signed is None and fpf is not None:
			wl = fpf.wl
			signed = fpf.signed
		elif not(wl is not None and signed is not None and fpf is None):
			raise ValueError("Constant: Bad combination of arguments")
		if wl < 2:
			raise ValueError("Constant: The word-length should be at least equal to 2")

		# store name
		if name:
			self._name = name
		else:
			self._name = str(value)

		# store the exact value given and it's approximated value with 2*wl bits in mpmath
		self._value = value
		mpvalue = mpf(value, prec=2*wl)     # !TODO: wl+1 bits should be enough

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
				self._mantissa = int(floor(mpvalue * 2 ** (wl - msb - 1) + 0.5))

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
			with workprec(20*wl):        # enough ??
				# set the msb
				if mpvalue > 0:
					corr = 1 - ldexp(1, -wl + (0 if signed else -1))
					msb = int(floor(log(mpvalue, 2) - log(corr, 2))) + (1 if signed else 0)
				else:
					corr = 1 + ldexp(1, -wl)
					msb = int(ceil(log(-mpvalue, 2) - log(corr, 2)))
				# set the lsb and the mantissa
				lsb = msb + 1 - wl
				self._mantissa = int(floor(ldexp(mpvalue, -lsb) + 0.5))


		elif method == 'threshold':

			with workprec(20*wl):       # enough?
				# compute wmin
				if mpvalue > 0:
					fr = 2**frac(log(mpvalue, 2))
					if fr < 1:
						wmin = int(floor(-log(1 - fr, 2))) + (1 if signed else 0)
					else:
						wmin = 0
				else:
					fr = 2**frac(log(-mpvalue, 2)+1)
					if fr > 1:
						wmin = int(floor(-log(fr - 1, 2)) + 1)
					else:
						wmin = 0
				# compute msb
				if mpvalue > 0:
					msb = int(floor(log(mpvalue, 2))) + (1 if signed else 0) + (1 if wl<wmin else 0)
				else:
					msb = int(ceil(log(-mpvalue, 2))) + (1 if wl<wmin else 0)
				# compute lsb and mantissa
				lsb = msb + 1 - wl
				self._mantissa = int(floor(ldexp(mpvalue, -lsb) + 0.5))


		else:

			def roundNearestTieUp(x, prec):
				t = mpf(x, prec=2*prec)
				return mpf(ldexp( (-1 if t<0 else 1) * t.man*2+1, t.exp-1), prec=prec, rounding='f')

			# since the value is already transformed in floating-point (mantissa + exponent) with mpmath
			# we can use that mantissa and exponent (be careful of the two's complement asymmetry, -2^p is ok with msb=p)

			with workprec(20*wl):

				# floating-point with the right word-length
				#fl = mpf(value, prec=wl - (1 if signed else 0))
				fl = roundNearestTieUp(value, prec=wl - (1 if signed else 0))       # round to nearest tie up
				# since mpmath do not have the integral significant (with MSB=1), we take the normalized significant
				# and build the mantissa (M) and exponent (e)
				m,ep = frexp(fl)
				M = ldexp(m, wl - (1 if signed else 0))
				e = ep - wl + (1 if signed else 0)
				# FxP mantissa, msb and lsb
				self._mantissa = int(M)
				lsb = e
				msb = wl + lsb - 1
				if self._mantissa == -2**(wl-2):
					# recompute the mantissa with one extra bit
					#fl = mpf(value, prec=wl)
					fl = roundNearestTieUp(value, prec=wl)
					m, _ = frexp(fl)
					M = ldexp(m, wl)
					# and adapt msb and lsb if we can
					if M == -2**(wl-1):
						lsb -= 1
						msb -= 1
						self._mantissa = int(M)




		# # check if the mantissa is valid when a fpf is given
		# if (not signed and not (0 <= self._mantissa < 2 ** wl) or (signed and not (-2 ** (wl - 1) <= self._mantissa < 2 ** (wl - 1)))):
		# 	raise ValueError("given FPF cannot represent value")
		# if self._mantissa == 0:
		# 	# TODO: add an option to return a null constant rather raise an exception
		# 	raise ValueError("The FPF is not enough to represent the constant without underflow !")

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
		return "<Constant(%s): %d*2**%d>" % (self._name, self._mantissa, self._FPF.lsb)

	def __repr__(self):
		return str(self)