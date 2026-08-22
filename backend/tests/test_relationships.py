import uuid


def _create_merchant_and_products_with_auth(client):
    """Helper to create a merchant, authenticated user, and two products."""
    email = f"rel_{uuid.uuid4().hex[:6]}@example.com"
    m_res = client.post("/api/merchants", json={
        "name": "Rel Store",
        "business_name": "Rel Ltd",
        "email": email,
    })
    m_id = m_res.json()["id"]

    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "role": "merchant_admin",
            "merchant_id": m_id,
        },
    )
    login_res = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    p1 = client.post(f"/api/merchants/{m_id}/products", json={
        "sku": "P1", "name": "Source Product", "description": "Src", "category": "A", "price": 100.00
    }, headers=headers).json()

    p2 = client.post(f"/api/merchants/{m_id}/products", json={
        "sku": "P2", "name": "Target Product", "description": "Tgt", "category": "B", "price": 200.00
    }, headers=headers).json()

    return m_id, p1["id"], p2["id"], headers


def test_create_and_get_relationship(client):
    """Test creating and retrieving valid product relationship."""
    _, p1_id, p2_id, headers = _create_merchant_and_products_with_auth(client)

    rel_payload = {
        "target_product_id": p2_id,
        "relationship_type": "cross_sell",
        "score": 0.85,
        "reason": "Frequently paired together",
    }
    res = client.post(f"/api/products/{p1_id}/relationships", json=rel_payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["relationship_type"] == "cross_sell"
    assert data["score"] == "0.85"

    # Retrieve relationships
    get_res = client.get(f"/api/products/{p1_id}/relationships", headers=headers)
    assert get_res.status_code == 200
    assert len(get_res.json()) == 1


def test_prevent_self_relationship(client):
    """Test preventing self-referential product relationship."""
    _, p1_id, _, headers = _create_merchant_and_products_with_auth(client)

    res = client.post(f"/api/products/{p1_id}/relationships", json={
        "target_product_id": p1_id,
        "relationship_type": "upsell",
        "score": 0.90,
    }, headers=headers)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "BAD_REQUEST"


def test_prevent_cross_merchant_relationship(client):
    """Test preventing relationships between products of different merchants."""
    _, p1_id, _, headers1 = _create_merchant_and_products_with_auth(client)

    # Create second merchant & product & user
    email2 = f"m2_{uuid.uuid4().hex[:6]}@example.com"
    m2_res = client.post("/api/merchants", json={
        "name": "Merchant 2",
        "business_name": "M2 Ltd",
        "email": email2,
    })
    m2_id = m2_res.json()["id"]
    client.post("/api/auth/register", json={"email": email2, "password": "Password123!", "role": "merchant_admin", "merchant_id": m2_id})
    token2 = client.post("/api/auth/login", json={"email": email2, "password": "Password123!"}).json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    p3_res = client.post(f"/api/merchants/{m2_id}/products", json={
        "sku": "P3", "name": "Other Merchant Prod", "description": "Desc", "category": "C", "price": 300.00
    }, headers=headers2)
    p3_id = p3_res.json()["id"]

    res = client.post(f"/api/products/{p1_id}/relationships", json={
        "target_product_id": p3_id,
        "relationship_type": "cross_sell",
        "score": 0.70,
    }, headers=headers1)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "BAD_REQUEST"
