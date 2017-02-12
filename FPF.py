# coding=utf8

"""Class FPF to store a Fixed-Point Format

A fixed-point format is determined by a signed-property (signed or unsigned) and two of the three following parameters:
- wordlength (wl)
- most significant bit
- least significant bit"""


__author__ = "Thibault Hilaire, Benoit Lopez"
__copyright__ = "Copyright 2015, FIPOgen Project, LIP6"
__credits__ = ["Thibault Hilaire", "Benoit Lopez"]

__license__ = "CECILL-C"
__version__ = "0.4"
__maintainer__ = "Thibault Hilaire"
__email__ = "thibault.hilaire@lip6.fr"
__status__ = "Beta"



import re
from mpmath import workprec, ldexp, nint


reobj_q = re.compile("^([su]?)Q([+-]?[0-9]+)\.([+-]?[0-9]+)$")		    # Q-notation
reobj_p = re.compile("^([su]?)\(([+-]?[0-9]+),([+-]?[0-9]+)\)$")		# parenthesis-notation


class FPF(object):
	"""Fixed-Point Format class
	
	Attributes:
		wl : wordlength
		msb: most significant bit
		lsb: least significant bit
		signed (boolean): indicates if the format is signed (True) or unsigned (False)
	"""

	def __init__(self, wl=None, msb=None, lsb=None, signed=True, formatStr=None):
		"""Constructor for a FPF object
		can be constructed from wordlength, msb and lsb (only 2 of the 3 are required), *but also* from a string (formatStr)
		
		Args:
			wl: wordlength
			msb: most significant bit
			lsb: least significant bit
			signed (boolean): indicates if the format is signed (True) or unsigned (False)
			formatStr (string): a string describing the FPF, with the Q-notation ("Q3.8", "uQ8.3", ...) or the Parentheses-notation ("(3,-4)", "u(8,0"), ...)
		Returns:
			a FPF object
		Raises:
			ValueError, when the format is not possible (lsb>msb, wl<1, etc...)	
		"""
		# check if FPF should be construct from format string
		if formatStr:
			fmt_q = reobj_q.match(formatStr)		# check Q-notation
			fmt_p = reobj_p.match(formatStr)		# check Parentheses-notation
			if fmt_q:
				signed, msb, lsb = fmt_q.groups()
				signed = (signed != 'u')
				msb = int(msb)-1
				lsb = -int(lsb)
				wl = msb + 1 - lsb
			elif fmt_p:
				signed, msb, lsb = fmt_p.groups()
				signed = (signed != 'u')
				msb = int(msb)
				lsb = int(lsb)
				wl = msb + 1 - lsb
			else:
				raise ValueError("Wrong FPF: '%s' is a wrong format" % formatStr)

		# check if wl/msb/lsb are coherent
		if wl < (2 if signed else 1) and (wl is not None):
			raise ValueError("Wrong FPF: wordlength is incorrect (wl=%d)" % wl)
		
		# When wl, msb and lsb are all given, check if wl ==  msb+1-lsb
		elif wl is not None and msb is not None and lsb is not None:
			if wl != (msb + 1 - lsb):
				raise ValueError("Wrong FPF: wl, msb and lsb should satisfy wl = msb +1 - lsb")
		
		# if only wl and msb are given, compute lsb
		elif wl is not None and msb is not None and lsb is None:
			lsb = msb + 1 - wl
			
		# if only wl and lsb are given, compute msb
		elif wl is not None and lsb is not None and msb is None:
			msb = wl + lsb - 1
			
		# if only msb and lsb are given, compute wl
		elif wl is None and lsb is not None and msb is not None:
			wl = msb + 1 - lsb
		
		else:
			raise ValueError('Wrong FPF: Not enough values are given (msb/lsb/wl')
		
		# store the values
		self._wl = wl
		self._msb = msb
		self._lsb = lsb
		self._signed = signed

		
	@property
	def msb(self):
		"""Returns the Most Significant Bit"""
		return self._msb


	@property    
	def lsb(self):
		"""Returns the Least Significant Bit"""
		return self._lsb

	
	@property
	def wl(self):
		"""Returns the Wordl-length"""
		return self._wl


	@property
	def signed(self):
		"""Returns the sign (True->signed, False->unsigned)"""
		return self._signed

			
	def wml(self):
		"""Returns the tuple (wl,msb,lsb)"""
		return self._wl, self._msb, self._lsb


	def __str__(self):
		return self.ParenthesisNotation()

		
	def __repr__(self):
		return "FPF( wl=%d, msb=%d, lsb=%d, signed=%s)" % (self._wl, self._msb, self._lsb, self._signed)


	def Qnotation(self):
		"""Returns the Q-notation (ex. "Q5.6") """
		return "%sQ%d.%d" % ('u'*(not self._signed), self._msb+1, -self._lsb)

	
	def ParenthesisNotation(self):
		"""Returns the Parentheses-notation (ex. "(5,-6)") """
		return "%s(%d,%d)" % ('u'*(not self._signed), self._msb, self._lsb)

		



	def minmax(self):
		"""Gives the interval a variable of this FPF may belong to.
		Returns:
			a tuple (min, max)
		"""
		with workprec(self._wl+1):      # wl bits is enough
			if self._signed:
				return -ldexp(1, self._msb), ldexp(1, self._msb) - ldexp(1, self.lsb)
			else:
				return 0, ldexp(1, self._msb+1) - ldexp(1, self.lsb)
			
	
	def LaTeX(self, y_origin=0, colors=None,  binary_point=False, label='no', notation='mlsb', numeric=False, intfrac=False, power2=False, hatches=None, bits=None, x_shift=0, drawMissing=False, **_):
		"""Generate the LaTeX version of the FPF -> only a grid, composed of sign, integer and fractional bits
		
		Each square is 1x1 square, and the point (0,y_origin) correspond to the binary-point position
		
		Arguments:
			- y_origin: y-coordinate of the origin (binary point position)
			- color: indicates the color theme, ie a 3-tuple with the colors of the sign, integer and fractional parts. 
				If None, the colors are set using tikzstyles named 'sign', 'integer' and 'fractional' (so must be assigned elsewhere with "\tikzstyle{xxx}=[...]")
			- binary_point: (boolean) indicates if the binary point is displayed
			- label: indicates where to display the label ('left'/'right'/'above'/'below' or 'no' if the label should not be displayed)
			- notation: use MSB/LSB notation if 'mlsb', or integer/fractional part if 'ifwl'
			- numeric: (boolean) display numeric values (instead of symbolic) if True
			- intfrac: (boolean) display integer/fractional parts if True
			- power2: (boolean) display power-of-2 if True
			- hatches: None if no hatches are displayed, otherwise hatches is a pair (msb,lsb) and hatches should be displayed for bits < msb and bits > lsb
			- bits: None if no value for the bits is displayed, or a string of "0" and "1" giving the bit values to be displayed
			- maxWL: (int) maximum wordlength to be plot. If the FPF has a longer wordlength, then some dots are plots, and not all the bits are exhibited
			- drawMissing: (boolean) draw the bits between the FPF and the binary-point position (when the FPF doesn't contain the binary-point), so that these "missing bits" can be shown
		"""
		# prepare the colors
		if colors:
			colors = ['fill='+c for c in colors]
		else:
			colors = ('sign', 'integer', 'fractional')
		pattern = 'pattern=north west lines, pattern color=blue'
		if not hatches:
			hatches = (float('inf'), float('-inf'))			# hack to set msb=infty and lsb=-infty when hatches are not displayed
		# prepare labels (numerical values, msb/lsb, integer/fractional parts, etc.)
		# fpf_str: string describing the FPF used for the label
		if numeric:
			fpf_str = self.Qnotation() if notation == 'ifwl' else self.ParenthesisNotation()
		else:
			if notation == 'ifwl':
				fpf_str = 'u'*(not self._signed) + 'Qi.f'
			else:
				fpf_str = 'u'*(not self._signed) + '(m,\ell)'
		# str_integer/frac/wl: used in the integer/frac part to display the integer/fractional part and the wordlength
		str_wl = 'w'
		if numeric:
			str_wl = str_wl+'='+str(self._wl)
		if notation == 'ifwl':
			str_integer = 'i' if self._msb > 0 else '-i'
			str_frac = 'f' if self._lsb < 0 else '-f'
			if numeric:
				str_integer = str_integer+'='+str(abs(self._msb+1))
				str_frac = str_frac+'='+str(abs(self._lsb))
		else:
			str_integer = 'm+1' if self._msb > 0 else '-m-1'
			str_frac = '-\ell' if self._lsb < 0 else '\ell'
			if numeric:
				str_integer = str_integer+'='+str(abs(self._msb+1))
				str_frac = str_frac+'='+str(abs(self._lsb))
		# str_lsb/msb to display the power of 2
		if numeric:
			str_lsb = self._lsb
			str_msb = self._msb
			str_msbm1 = self._msb - 1
		else:
			if notation == 'ifwl':
				str_lsb = '-f'
				str_msb = 'i-1'
				str_msbm1 = 'i-2'
			else:
				str_lsb = '\ell'
				str_msb = 'm'
				str_msbm1 = 'm-1'
		# Comment
		st = "\t%FPF="+self.ParenthesisNotation() + "\n"
		# create a generator of the bits values (or a generator of a None list)
		bits = (b for b in bits) if bits else (None for _ in range(self._wl))
		# One rectangle per bit
		firstSigned = self._signed		# True if self is signed. Still True if we do not enter in the 1st loop (when integer part<0)
		for m in range(-self._msb-1, min(0, -self._lsb)):
			st += "\t\\draw (%f,%f) rectangle ++(1,1) [%s,%s] node[midway] {%s};\n" % (m+x_shift, y_origin, colors[0 if firstSigned else 1], pattern if -m > hatches[0]+1 else '', bits.next() or ('s' if firstSigned else ''))
			firstSigned = False
		for l in range(-min(0, self._msb+1), -self._lsb):
			st += "\t\\draw (%f,%f) rectangle ++(1,1) [%s,%s] node[midway] {%s};\n" % (l+x_shift, y_origin, colors[0 if firstSigned else 2], pattern if -l < hatches[1]+1 else '', bits.next() or ('s' if firstSigned else ''))
			firstSigned = False
		# dashed rectangle for "missing bits" around the binary-point position
		if drawMissing:
			for m in range(0, -self._msb-1):
				st += "\t\\draw (%f,%f) [dashed] rectangle ++(1,1);\n" % (m+x_shift, y_origin)
			for l in range(-self._lsb-1, 0):
				st += "\t\\draw (%f,%f) [dashed] rectangle ++(1,1);\n" % (l+x_shift, y_origin)
		# Binary-point position
		if binary_point:
			st += '\t\\draw[black,fill] (0,%f) circle [radius=0.1cm];\n' % (y_origin, )
		# Label format
		if label == 'above':
			st += '\t\\draw (%f,%f) node[above] {$%s$};\n' % ((-self._lsb-self._msb-1)/2, y_origin+1, fpf_str)
		elif label == 'below':
			st += '\t\\draw (%f,%f) node[below] {$%s$};\n' % ((-self._lsb-self._msb-1)/2, y_origin, fpf_str)
		elif label == 'right':
			st += '\t\\draw (%f,%f) node[right] {$%s$};\n' % (0 if drawMissing and self._lsb > 0 else -self._lsb, y_origin+0.5, fpf_str)
		elif label == 'left':
			st += '\t\\draw (%f,%f) node[left] {$%s$};\n' % (0 if drawMissing and self._msb < 0 else -self._msb-1, y_origin+0.5, fpf_str)
		# Integer/fractional part display (with arrows)
		if intfrac:
			if self._msb+1 != 0:
				y_msb = y_origin - (0.35 if self._msb+1 > 0 else 0.70)
				st += '\t\\draw[|<->|] (%f,%f) -- (0,%f) node[midway,fill=white!30] {$%s$};\n' % (-self._msb-1, y_msb, y_msb, str_integer)
			if self._lsb != 0:
				# fractional part: from -min(0,self._alpha) to  self._gamma
				y_lsb = y_origin - (0.35 if self._lsb < 0 else 0.70)
				st += '\t\\draw[|<->|] (0,%f) -- (%f,%f) node[midway,fill=white!30] {$%s$};\n' % (y_lsb, -self._lsb, y_lsb, str_frac)
			st += '\t\\draw[|<->|] (%f,%f) -- (%f,%f) node[midway,fill=white!30] {$%s$};\n' % (-self._msb-1, y_origin-0.7, -self._lsb, y_origin-0.7, str_wl)
		# Display the power of 2
		if power2:
			# sign bit : -2^(msb)
			if self._signed:
				st += "\t\\draw (%f,%f) node[above] {$-2^{%s}$};\n" % (-self._msb-1+0.5, y_origin+1, str_msb)
			# 2^0
			if self._msb-1 > 0 > self._lsb:
				st += "\t\\draw (-0.5,%f) node[above] {$2^0$};\n" % (y_origin+1, )
			# 2^-1
			if self._msb-1 > -1 > self._lsb:
				st += "\t\\draw (0.5,%f) node[above] {$2^{-1}$};\n" % (y_origin+1,)
			# most signifiant bit (excluding sign bit) : 2^(msb-1) or 2^msb
			st += "\t\\draw (%f,%f) node[above] {$2^{%s}$};\n" % (-(self._msb+1 if self._signed else self._msb+2)+1.5, y_origin+1, str_msbm1 if self._signed else str_msb)
			# less signifiant bit (excluding sign bit) : 2^lsb
			st += "\t\\draw (%f,%f) node[above] {$2^{%s}$};\n" % (-self._lsb-0.5, y_origin+1, str_lsb)
		
		# Returns the full string
		return st


	# def shift(self, d):
	# 	"""Right shift of d bits and decrease msb without changing beta."""
	# 	# TODO: warning si le shift est negatif
	# 	self._msb += d
	# 	self._lsb += d


	# def approx(self, r):
	# 	"""Convert a "real" number in this FPF
	# 	Args:
	# 		r: number to convert in this FPF
	# 	Returns:
	# 		an approximation of r, expressed in this FPF
	# 	"""
	# 	# !FIXME: should we check that r is in [ -2^m - 2^(l-1), 2^m - 2^(l-1) ] for signed (and [ 0, 2^(m+1) - 2^(l-1) ] ??
	# 	# nint is `round to nearest int` (ie round)
	# 	return ldexp(1, self._lsb) * nint(ldexp(r, -self._lsb))



	# def __copy__(self):
	# 	"""Returns a copy of a given FPF"""
	# 	# !TODO: check if necessary (there is a lot of copy in Adder, Multiplier, etc.)
	# 	return FPF(wl=self._wl, msb=self._msb, signed=self._signed)
