import unittest
import os
import sqlite3
import json
from datetime import date
from codes import database_operations

import tempfile

# Use of temporary file instead of :memory: because the app opens/closes connection on every call
# which wipes an in-memory DB.
class TestDatabaseOperations(unittest.TestCase):
    def setUp(self):
        """Set up a fresh database before each test."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        database_operations.DATABASE_NAME = self.db_path
        # Reset the database connection/tables
        database_operations.create_tables()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_create_connection(self):
        conn = database_operations.create_connection()
        self.assertIsInstance(conn, sqlite3.Connection)
        conn.close()

    def test_add_and_get_product(self):
        # Test adding a product
        result = database_operations.add_product_db("12345", "Test Product", 10.5, 100)
        self.assertTrue(result)

        # Test retrieving the product
        product = database_operations.get_product_info_db("12345")
        self.assertIsNotNone(product)
        self.assertEqual(product[0], "12345")
        self.assertEqual(product[1], "Test Product")
        self.assertEqual(product[2], 10.5)
        self.assertEqual(product[3], 100)

    def test_add_duplicate_product(self):
        database_operations.add_product_db("12345", "Test Product", 10.5, 100)
        # Try adding the same barcode again
        result = database_operations.add_product_db("12345", "Another Name", 20.0, 50)
        self.assertFalse(result)

    def test_update_product(self):
        database_operations.add_product_db("12345", "Old Name", 10.0, 10)
        
        # Update name and stock
        result = database_operations.update_product_db("12345", product_name="New Name", stock=50)
        self.assertTrue(result)
        
        product = database_operations.get_product_info_db("12345")
        self.assertEqual(product[1], "New Name")
        self.assertEqual(product[3], 50)
        self.assertEqual(product[2], 10.0) # Price should remain unchanged

    def test_delete_product(self):
        database_operations.add_product_db("12345", "To Delete", 10.0, 10)
        
        result = database_operations.delete_product_db("12345")
        self.assertTrue(result)
        
        product = database_operations.get_product_info_db("12345")
        self.assertIsNone(product)

    def test_save_and_get_sales(self):
        cart = {
            "12345": {"isim": "Test Prod", "fiyat": 10.0, "adet": 2},
            "67890": {"isim": "Prod 2", "fiyat": 5.0, "adet": 1}
        }
        total = 25.0
        
        result = database_operations.save_sale_db(cart, total)
        self.assertTrue(result)
        
        sales = database_operations.get_all_sales_db()
        self.assertTrue(len(sales) > 0)
        latest_sale = sales[0]
        self.assertEqual(latest_sale[2], 25.0) # Total amount
        
        # Helper to get details
        details_json = database_operations.get_sale_details_db(latest_sale[0])
        details = json.loads(details_json)
        self.assertEqual(details["12345"]["isim"], "Test Prod")

    def test_get_product_based_report(self):
        # Setup data
        cart = {"12345": {"isim": "Report Item", "fiyat": 100.0, "adet": 1}}
        database_operations.save_sale_db(cart, 100.0)
        
        # Test report generation
        today = date.today().strftime('%Y-%m-%d')
        report = database_operations.get_product_based_report_db(today, today)
        
        self.assertIsInstance(report, list)
        self.assertTrue(len(report) > 0)
        self.assertEqual(report[0][0], "Report Item")

if __name__ == '__main__':
    unittest.main()
