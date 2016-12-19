import unittest
from FxP.FPF import FPF
from FxP.Constant import Constant


########################################################################
class Test_Constants(unittest.TestCase):
	""""""
	def test_construct(self):
		c = Constant( value=127, wl=8, signed=False)
		self.assertEqual( c.FPF.wml(), (8,6,-1) )
		self.assertEqual( c.integer, 254)

		c = Constant( value=127, wl=8)
		self.assertEqual( c.FPF.wml(), (8,7,0) )
		self.assertEqual( c.integer, 127)
		
		c = Constant( value=-127, wl=8, signed=True)
		self.assertEqual( c.FPF.wml(), (8,7,0) )
		self.assertEqual( c.integer, -127)
		
		c = Constant( value = 0.36567, wl=8)
		self.assertEqual( c.FPF.wml(), (8,-1,-8))
		self.assertEqual( c.integer, 94)
		self.assertEqual( c.approx, 94*2**-8)
		
		with self.assertRaises(ValueError):
			c = Constant( value=-12, wl=12, signed=False)

		c = Constant( value=127.78, wl=8, signed=False)
		self.assertEqual( c.FPF.wml(), (8,7,0) )
		self.assertEqual( c.integer, 128)		
		
		# particular cases
		c = Constant( value=127.78, wl=8, signed=False)
		self.assertEqual( c.FPF.wml(), (8,7,0) )
		self.assertEqual( c.integer, 128)		
		c = Constant( value=-128.1, wl=8, signed=True)
		self.assertEqual( c.FPF.wml(), (8,7,0) )
		self.assertEqual( c.integer, -128)					
		c = Constant( value=127.7, wl=8, signed=True)
		self.assertEqual( c.FPF.wml(), (8,8,1) )
		self.assertEqual( c.integer, 64)			
		
		c = Constant( value = -64.25, wl=8, signed=True)
		self.assertEqual( c.FPF.wml(), (8,6,-1))
		self.assertEqual( c.integer, -128)
		c = Constant( value=-64.3, wl=8, signed=True)
		self.assertEqual( c.FPF.wml(), (8,6,-1) )
		self.assertEqual( c.integer, -128)					
		c = Constant( value=-64.5, wl=8, signed=True)
		self.assertEqual( c.FPF.wml(), (8,7,0) )
		self.assertEqual( c.integer, -65)		
		
		# construct with a given FPF
		with self.assertRaises(ValueError):
			c = Constant(value=258.54, wl=8,fpf=FPF(8,7,0))
		
if __name__ == '__main__':
	unittest.main()