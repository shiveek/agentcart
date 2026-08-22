import uuid


def _create_sample_product_with_auth(client):
    """Helper to create a test merchant, user, and product with auth headers."""
    email = f"inv_{uuid.uuid4().hex[:6]}@example.com"
    merchant_res = client.post("/api/merchants", json={
        "name": f"Inv Store {uuid.uuid4().hex[:4]}",
        "business_name": "Inv Ltd",
        "email": email,
    })
    merchant_id = merchant_res.json()["id"]

    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "role": "merchant_admin",
            "merchant_id": merchant_id,
        },
    )
    login_res = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    prod_res = client.post(f"/api/merchants/{merchant_id}/products", json={
        "sku": f"SKU-{uuid.uuid4().hex[:4]}",
        "name": "Inventory Item",
        "description": "Item description",
        "category": "Gadgets",
        "price": 500.00,
        "initial_quantity": 20,
    }, headers=headers)
    return prod_res.json()["id"], headers


def test_get_and_update_inventory(client):
    """Test inventory retrieval and valid update."""
    product_id, headers = _create_sample_product_with_auth(client)

    # Fetch initial inventory
    inv_res = client.get(f"/api/products/{product_id}/inventory", headers=headers)
    assert inv_res.status_code == 200
    data = inv_res.json()
    assert data["quantity"] == 20
    assert data["reserved_quantity"] == 0
    assert data["available_quantity"] == 20

    # Update inventory
    update_res = client.put(f"/api/products/{product_id}/inventory", json={
        "quantity": 50,
        "reserved_quantity": 10,
        "reorder_level": 5,
    }, headers=headers)
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["quantity"] == 50
    assert updated["reserved_quantity"] == 10
    assert updated["available_quantity"] == 40


def test_invalid_inventory_reservations(client):
    """Test updating reserved_quantity > total quantity returns validation error."""
    product_id, headers = _create_sample_product_with_auth(client)

    # Reserved > total
    res = client.put(f"/api/products/{product_id}/inventory", json={
        "quantity": 10,
        "reserved_quantity": 15,
    }, headers=headers)
    assert res.status_code == 422  # Pydantic model validator catch
