import json
from os.path import isfile, join
from os import listdir
from shopify import Metafield, Product
from exporters.shopify import ShopifyExporter
from exporters.shopify_multi_vendor import ShopifyMultiVendorExporter
from importer.opencart import OpencartImporter
from importer.shopify_multi_vendor import ShopifyMultiVendorImporter
from models.open_cart.openCartProduct import OpenCartProduct_from_dict
from models.shopify_multi_vendor.shopify_multi_vendor_product import mvm_product_from_dict


def migrate_products_from_open_cart_to_mvm(test_item_count=0):
    importer = OpencartImporter()
    products = importer.fetch_products(total_products=3280)

    # write products to  json file
    json.dump(products, open(
        "source/opencart/products/opencart_products.json", "w"))

    # read products from json file
    products = json.load(open(
        "source/opencart/products/opencart_products.json", "r"))

    open_cart_products = [
        OpenCartProduct_from_dict(
            product) for product in products
    ]

    # loop over products
    items_to_migrate_count = test_item_count if test_item_count > 0 else len(
        open_cart_products)
    shopify_mvm_products = [
        open_cart_products[index].to_shipify_multi_vendor_product() for index in range(items_to_migrate_count)]

    exporter = ShopifyMultiVendorExporter()

    failures = []
    successes: dict = {}
    try:
        for productIndex in range(0, len(shopify_mvm_products)):
            print(f"productIndex: {productIndex}")
            result = exporter.create_product(
                shopify_mvm_products[productIndex])
            if result.get("code", None):
                print(result)
                failures.append(shopify_mvm_products[productIndex].to_dict())
                json.dump(failures, open(
                    "output/failures/products/opencart_products_failures.json", "w"))
            else:
                if result["product"]["id"]:
                    successes[shopify_mvm_products[productIndex].product_name] = result["product"]
                    json.dump(successes, open(
                        "output/successes/products/opencart_products_successes.json", "w"))
            productIndex += 1
    except Exception as e:
        print(e)


def retry_failed_products(path_to_failurs_file: str, test_item_count=0):
    failures = json.load(open(path_to_failurs_file, "r"))
    shopify_mvm_products = [
        mvm_product_from_dict(failure) for failure in failures
    ]

    # push to shopify Multi Vendor
    exporter = ShopifyMultiVendorExporter()

    failures = []
    successes: dict = {}

    items_to_migrate_count = test_item_count if test_item_count > 0 else len(
        shopify_mvm_products)

    try:
        for productIndex in range(0, items_to_migrate_count):
            print(f"productIndex: {productIndex}")
            result = exporter.create_product(
                shopify_mvm_products[productIndex])
            if result.get("code", None):
                print(result)
                failures.append(shopify_mvm_products[productIndex].to_dict())
                json.dump(failures, open(
                    "output/failures/products/opencart_products_failures.json", "w"))
            else:
                if result["product"]["id"]:
                    successes[shopify_mvm_products[productIndex]
                              .product_name] = result["product"]
                    json.dump(successes, open(
                        "output/successes/products/opencart_products_successes.json", "w"))
            productIndex += 1
    except Exception as e:
        print(e)


def fetch_all_products_from_shopify_multi_vendor(product_count=0):
    importer = ShopifyMultiVendorImporter()
    products = importer.fetch_products(total_products=product_count)
    # write to json file
    json.dump(products, open(
        "source/shopify_multi_vendor/products/shopify_multi_vendor_products.json", "w"))


def add_download_link_meta_field(shopify_product_id, link):
    # product = Product.find(shopify_product_id)
    metafield = Metafield(
        {
            'type': 'url',
            'namespace': 'my_fields',
            'key': 'download_link',
            'value': link
        },
        prefix_options={
            'resource': 'products',
            'resource_id': shopify_product_id
        }
    )
    return metafield.save()


def update_products(test_item_count=0):
    exporter = ShopifyExporter()
    exporter.authentication()

    # read shopify product IDs & filenames from json file
    products_ids = json.load(open(
        "source/opencart/products/opencart_products.json", "r"))

    # loop over products
    items_to_update_count = test_item_count if test_item_count > 0 else len(
        products_ids)

    failures = []
    successes = []
    try:
        for productIndex in range(0, items_to_update_count):
            print(f"productIndex: {productIndex}")
            result = add_download_link_meta_field("prodict id", "link")
            if result is (not True):
                print(result)
                failures.append(products_ids[productIndex])
                json.dump(failures, open(
                    "output/failures/products/opencart_products_update_failures.json", "w"))
            else:
                if result:
                    successes.append(products_ids[productIndex])
                    json.dump(successes, open(
                        "output/successes/products/opencart_products_update_successes.json", "w"))
            productIndex += 1
    except Exception as e:
        print(e)


def main():
    print("Welcome to Product Migration Menu")
    print("1. Migrate Products from OpenCart to Shopify Multi Vendor Market place")
    print("2. Retry Failures")
    print("3. Fetch all products from Shopify Multi Vendor Market place")
    print("4. Update products download links")

    choice = int(input("Enter your choice: "))

    if choice == 1:
        test_item_count = int(
            input("Enter the number of items to migrate (0 for all): "))
        migrate_products_from_open_cart_to_mvm(
            test_item_count=test_item_count)
    elif choice == 2:
        print("Retry Failures")
        print("Enter s.no of the file to retry: ")
        # list all files in /output/failures
        path_to_failures_file = "output/failures/products/"
        onlyfiles = [f for f in listdir(path_to_failures_file) if isfile(
            join(path_to_failures_file, f))]

        for fileIndex in range(len(onlyfiles)):
            print(
                f"{fileIndex + 1}: {path_to_failures_file}{onlyfiles[fileIndex]}")
        choice = int(input("Enter your choice: "))
        test_item_count = int(
            input("Enter the number of items to migrate (0 for all): "))
        retry_failed_products(
            f"{path_to_failures_file}{onlyfiles[choice - 1]}", test_item_count)
    elif choice == 3:
        test_item_count = int(
            input("Enter the number of items to fetch (more then 250) : "))
        fetch_all_products_from_shopify_multi_vendor(
            product_count=test_item_count)
    elif choice == 4:
        print("Update products download links")
        print(add_download_link_meta_field(
            "6827641176157", "https://www.google.com"))


# Call Main
main()
