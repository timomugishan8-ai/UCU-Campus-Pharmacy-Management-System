"""Member 2 tests: Branch and Stock domain objects.

Branch tests live here because branch and stock are one allocation unit
("medicine, branch and stock" domain): a stock row is meaningless without
its branch. Covers the invariants from the exam domain rules: branch
identification, per-branch quantities, never-negative stock, positive
receipts, fulfilment checks and the low-stock boundary.
"""

import unittest

from domain.branch import Branch, BranchError
from domain.stock import InsufficientStockError, Stock, StockError


class BranchTests(unittest.TestCase):
    """Object-level rules of the Branch entity."""

    def test_construction_with_name_only_is_unpersisted(self):
        branch = Branch("Main Campus Pharmacy")
        self.assertEqual(branch.branch_name, "Main Campus Pharmacy")
        self.assertIsNone(branch.branch_id)

    def test_construction_with_id(self):
        branch = Branch("East Campus Pharmacy", 2)
        self.assertEqual(branch.branch_id, 2)

    def test_name_is_stripped(self):
        self.assertEqual(Branch("  Main  ").branch_name, "Main")

    def test_blank_or_non_string_name_is_rejected(self):
        for bad_name in ("", "   ", None, 42):
            with self.subTest(name=bad_name):
                with self.assertRaises(BranchError):
                    Branch(bad_name)

    def test_invalid_branch_id_is_rejected(self):
        for bad_id in (0, -1, "1", 1.5, True):
            with self.subTest(branch_id=bad_id):
                with self.assertRaises(BranchError):
                    Branch("Name", bad_id)

    def test_branch_error_is_a_value_error_for_the_gui_boundary(self):
        # Screens catch ValueError; the hierarchy must satisfy that.
        self.assertTrue(issubclass(BranchError, ValueError))
        with self.assertRaises(ValueError):
            Branch("")

    def test_attributes_are_read_only(self):
        branch = Branch("Main", 1)
        with self.assertRaises(AttributeError):
            branch.branch_name = "Other"
        with self.assertRaises(AttributeError):
            branch.branch_id = 2

    def test_to_dict_and_from_dict_round_trip(self):
        branch = Branch("Main Campus Pharmacy", 1)
        restored = Branch.from_dict(branch.to_dict())
        self.assertEqual(restored, branch)
        self.assertEqual(restored.branch_id, 1)

    def test_equality(self):
        self.assertEqual(Branch("Main", 1), Branch("Main", 1))
        self.assertNotEqual(Branch("Main", 1), Branch("Main", 2))
        self.assertNotEqual(Branch("Main", 1), Branch("Other", 1))


class StockTests(unittest.TestCase):
    """Object-level rules of the Stock entity."""

    def test_construction_defaults_to_zero_quantity(self):
        stock = Stock("MED-001", 1)
        self.assertEqual(stock.quantity, 0)

    def test_branch_specific_rows_are_independent(self):
        # The same medicine at two branches never shares a quantity.
        main = Stock("MED-001", 1, 10)
        satellite = Stock("MED-001", 2, 60)
        main.receive(5)
        self.assertEqual(main.quantity, 15)
        self.assertEqual(satellite.quantity, 60)

    def test_negative_or_non_integer_quantity_is_rejected(self):
        for bad_quantity in (-1, 2.5, "5", None, True):
            with self.subTest(quantity=bad_quantity):
                with self.assertRaises(StockError):
                    Stock("MED-001", 1, bad_quantity)

    def test_invalid_identity_is_rejected(self):
        with self.assertRaises(StockError):
            Stock("", 1, 0)          # blank medicine code
        with self.assertRaises(StockError):
            Stock("MED-001", 0, 0)   # branch id must be positive
        with self.assertRaises(StockError):
            Stock("MED-001", 1, -1)

    def test_receive_adds_positive_quantity(self):
        stock = Stock("MED-001", 1, 10)
        stock.receive(5)
        self.assertEqual(stock.quantity, 15)

    def test_receive_rejects_zero_negative_and_fractional_amounts(self):
        stock = Stock("MED-001", 1, 10)
        for bad_amount in (0, -5, 2.5, "5", None, True):
            with self.subTest(amount=bad_amount):
                with self.assertRaises(StockError):
                    stock.receive(bad_amount)
        # A rejected receipt changes nothing.
        self.assertEqual(stock.quantity, 10)

    def test_can_fulfil_boundaries(self):
        stock = Stock("MED-001", 1, 10)
        self.assertTrue(stock.can_fulfil(10))   # exact amount is allowed
        self.assertTrue(stock.can_fulfil(3))
        self.assertFalse(stock.can_fulfil(11))
        with self.assertRaises(StockError):
            stock.can_fulfil(0)

    def test_decrease_reduces_quantity(self):
        stock = Stock("MED-001", 1, 10)
        stock.decrease(4)
        self.assertEqual(stock.quantity, 6)

    def test_decrease_to_zero_is_allowed(self):
        stock = Stock("MED-001", 1, 10)
        stock.decrease(10)
        self.assertEqual(stock.quantity, 0)

    def test_decrease_below_zero_raises_and_changes_nothing(self):
        stock = Stock("MED-001", 1, 10)
        with self.assertRaises(InsufficientStockError):
            stock.decrease(11)
        # Quantity never becomes negative.
        self.assertEqual(stock.quantity, 10)

    def test_decrease_rejects_invalid_amounts(self):
        stock = Stock("MED-001", 1, 10)
        for bad_amount in (0, -1, 2.5, "5", None, False):
            with self.subTest(amount=bad_amount):
                with self.assertRaises(StockError):
                    stock.decrease(bad_amount)
        self.assertEqual(stock.quantity, 10)

    def test_insufficient_stock_error_is_a_stock_error(self):
        self.assertTrue(issubclass(InsufficientStockError, StockError))
        self.assertTrue(issubclass(StockError, ValueError))

    def test_low_stock_boundary_is_at_or_below_reorder_level(self):
        stock = Stock("MED-001", 1, 20)
        self.assertTrue(stock.is_low_stock(20))   # equal -> low stock
        stock.receive(1)
        self.assertFalse(stock.is_low_stock(20))  # above -> not low
        stock.decrease(2)
        self.assertTrue(stock.is_low_stock(20))   # below -> low stock

    def test_is_low_stock_rejects_invalid_reorder_level(self):
        stock = Stock("MED-001", 1, 5)
        for bad_level in (-1, 2.5, "10", True):
            with self.subTest(reorder_level=bad_level):
                with self.assertRaises(StockError):
                    stock.is_low_stock(bad_level)

    def test_to_dict_and_from_dict_round_trip(self):
        stock = Stock("MED-001", 2, 35)
        restored = Stock.from_dict(stock.to_dict())
        self.assertEqual(restored, stock)
        self.assertEqual(restored.quantity, 35)

    def test_from_dict_defaults_missing_quantity_to_zero(self):
        stock = Stock.from_dict({"medicine_code": "MED-001", "branch_id": 1})
        self.assertEqual(stock.quantity, 0)

    def test_attributes_are_read_only(self):
        stock = Stock("MED-001", 1, 10)
        with self.assertRaises(AttributeError):
            stock.quantity = 999
        with self.assertRaises(AttributeError):
            stock.medicine_code = "MED-002"


if __name__ == "__main__":
    unittest.main()
