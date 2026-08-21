import uuid


def _create_sample_merchant(client):
    """Helper to create a test merchant."""
    unique_email = f"merchant_{uuid.uuid4().hex[:8]}@test.com"
    payload = {
        "name": "Test Store",
        "business_name": "Test Store Ltd",
        "email": unique_email,
        "currency": "INR",
    }
    res = client.post("/api/merchants", json=payload)
    return res.json()["id"]


def test_create_and_get_product(client):
    """Test product creation and retrieval."""
    merchant_id = _create_sample_merchant(client)
    prod_payload = {
        "sku": "KB100",
        "name": "Gaming Keyboard",
        "description": "RGB Mechanical Keyboard",
        "category": "Keyboards",
        "price": 2999.00,
        "currency": "INR",
        "initial_quantity": 50,
        "reorder_level": 5,
    }
    res = client.post(f"/api/merchants/{merchant_id}/products", json=prod_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["sku"] == "KB100"
    assert data["price"] == "2999.00"
    product_id = data["id"]

    # Get single product
    get_res = client.get(f"/api/products/{product_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Gaming Keyboard"


def test_list_products_filtering_and_pagination(client):
    """Test product list search, category, price filtering, and pagination."""
    merchant_id = _create_sample_merchant(client)

    products = [
        {"sku": "P1", "name": "Alpha Phone", "description": "Flagship phone", "category": "Phones", "price": 49999.00, "initial_quantity": 10},
        {"sku": "P2", "name": "Beta Headset", "description": "Noise canceling", "category": "Audio", "price": 3499.00, "initial_quantity": 25},
        {"sku": "P3", "name": "Gamma Charger", "description": "Fast charger", "category": "Accessories", "price": 999.00, "initial_quantity": 100},
    ]

    for p in products:
        client.post(f"/api/merchants/{merchant_id}/products", json=p)

    # Search filter
    search_res = client.get(f"/api/merchants/{merchant_id}/products?search=Phone")
    assert search_res.status_code == 200
    assert search_res.json()["total"] == 1

    # Price filter
    price_res = client.get(f"/api/merchants/{merchant_id}/products?min_price=1000&max_price=5000")
    assert price_res.status_code == 200
    assert price_res.json()["total"] == 1
    assert price_res.json()["items"][0]["sku"] == "P2"

    # Pagination
    page_res = client.get(f"/api/merchants/{merchant_id}/products?page=1&page_size=2")
    assert page_res.status_code == 200
    assert len(page_res.json()["items"]) == 2
    assert page_res.json()["total"] == 3


def test_delete_product(client):
    """Test product deactivation."""
    merchant_id = _create_sample_merchant(client)
    res = client.post(f"/api/merchants/{merchant_id}/products", json={
        "sku": "DEL1",
        "name": "Temporary Item",
        "description": "Will be deleted",
        "category": "Misc",
        "price": 100.00,
    })
    product_id = res.json()["id"]

    del_res = client.delete(f"/api/products/{product_id}")
    assert del_res.status_code == 200
    assert del_res.json()["is_active"] is False
