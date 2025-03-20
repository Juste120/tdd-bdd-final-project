######################################################################
# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        #
        # Uncomment this code once READ is implemented
        #

        # # Check that the location header was correct
        # response = self.client.get(location)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # new_product = response.get_json()
        # self.assertEqual(new_product["name"], test_product.name)
        # self.assertEqual(new_product["description"], test_product.description)
        # self.assertEqual(Decimal(new_product["price"]), test_product.price)
        # self.assertEqual(new_product["available"], test_product.available)
        # self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    #
    # ADD YOUR TEST CASES HERE
    #

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)

    
    def test_get_product(self):
    """It should Get a single Product"""
    # Créez un produit
    test_product = self._create_products(1)[0]
    
    # Faites une requête GET pour récupérer le produit
    response = self.client.get(f"{BASE_URL}/{test_product.id}")
    
    # Vérifiez que la réponse est HTTP 200 OK
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    # Vérifiez que les données retournées correspondent au produit créé
    data = response.get_json()
    self.assertEqual(data["name"], test_product.name)

    def test_get_product_not_found(self):
        """It should not Get a Product thats not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("was not found", data["message"])

def test_update_product(self):
    """It should Update an existing Product"""
    # Créez un produit
    test_product = ProductFactory()
    response = self.client.post(BASE_URL, json=test_product.serialize())
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    # Mettez à jour le produit
    new_product = response.get_json()
    new_product["description"] = "unknown"
    response = self.client.put(f"{BASE_URL}/{new_product['id']}", json=new_product)
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    # Vérifiez que les données ont été mises à jour
    updated_product = response.get_json()
    self.assertEqual(updated_product["description"], "unknown")

def test_delete_product(self):
    """It should Delete a Product"""
    # Créez 5 produits
    products = self._create_products(5)
    product_count = self.get_product_count()
    test_product = products[0]
    
    # Supprimez le produit
    response = self.client.delete(f"{BASE_URL}/{test_product.id}")
    self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    self.assertEqual(len(response.data), 0)
    
    # Vérifiez que le produit a été supprimé
    response = self.client.get(f"{BASE_URL}/{test_product.id}")
    self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # Vérifiez que le nombre de produits a diminué
    new_count = self.get_product_count()
    self.assertEqual(new_count, product_count - 1)

def test_get_product_list(self):
    """It should Get a list of Products"""
    # Créez 5 produits
    self._create_products(5)
    
    # Faites une requête GET pour lister tous les produits
    response = self.client.get(BASE_URL)
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    # Vérifiez que 5 produits sont retournés
    data = response.get_json()
    self.assertEqual(len(data), 5)

def test_query_by_name(self):
    """It should Query Products by name"""
    # Créez 5 produits
    products = self._create_products(5)
    test_name = products[0].name
    name_count = len([product for product in products if product.name == test_name])
    
    # Faites une requête GET pour lister les produits par nom
    response = self.client.get(BASE_URL, query_string=f"name={quote_plus(test_name)}")
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    # Vérifiez que les produits retournés correspondent au nom recherché
    data = response.get_json()
    self.assertEqual(len(data), name_count)
    for product in data:
        self.assertEqual(product["name"], test_name)

        

def test_query_by_category(self):
    """It should Query Products by category"""
    # Créez 10 produits
    products = self._create_products(10)
    category = products[0].category
    found = [product for product in products if product.category == category]
    found_count = len(found)
    
    # Faites une requête GET pour lister les produits par catégorie
    response = self.client.get(BASE_URL, query_string=f"category={category.name}")
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    # Vérifiez que les produits retournés correspondent à la catégorie recherchée
    data = response.get_json()
    self.assertEqual(len(data), found_count)
    for product in data:
        self.assertEqual(product["category"], category.name)

def test_query_by_availability(self):
    """It should Query Products by availability"""
    # Créez 10 produits
    products = self._create_products(10)
    available_products = [product for product in products if product.available is True]
    available_count = len(available_products)
    
    # Faites une requête GET pour lister les produits disponibles
    response = self.client.get(BASE_URL, query_string="available=true")
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    # Vérifiez que les produits retournés sont disponibles
    data = response.get_json()
    self.assertEqual(len(data), available_count)
    for product in data:
        self.assertEqual(product["available"], True)