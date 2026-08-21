import uuid


def _create_merchant_and_products(client):
    """Helper to create a merchant and two products."""
    m_res = client.post("/api/merchants", json={
        "name": "Rel Store",
        "business_name": "Rel Ltd",
        "email": f"rel_{uuid.uuid4().hex[:6]}@test.com",
    })
    m_id = m_res.json()["id"]

    p1 = client.post(f"/api/merchants/{m_id}/products", json={
        "sku": "P1", "name": "Source Product", "description": "Src", "category": "A", "price": 100.00
    }).json()

    p2 = client.post(f"/api/merchants/{m_id}/products", json={
        "sku": "P2", "name": "Target Product", "description": "Tgt", "category": "B", "price": 200.00
    }).json()

    return m_id, p1["id"], p2["id"]


def test_create_and_get_relationship(client):
    """Test creating and retrieving valid product relationship."""
    _, p1_id, p2_id = _create_merchant_and_products(client)

    rel_payload = {
        "target_product_id": p2_id,
        "relationship_type": "cross_sell",
        "score": 0.85,
        "reason": "Frequently paired together",
    }
    res = client.post(f"/api/products/{p1_id}/relationships", json=rel_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["relationship_type"] == "cross_sell"
    assert data["score"] == "0.85"

    # Retrieve relationships
    get_res = client.get(f"/api/products/{p1_id}/relationships")
    assert get_res.status_code == 200
    assert len(get_res.json()) == 1


def test_prevent_self_relationship(client):
    """Test preventing self-referential product relationship."""
    _, p1_id, _ = _create_merchant_and_products(client)

    res = client.post(f"/api/products/{p1_id}/relationships", json={
        "target_product_id": p1_id,
        "relationship_type": "upsell",
        "score": 0.90,
    })
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "BAD_REQUEST"


def test_prevent_cross_merchant_relationship(client):
    """Test preventing relationships between products of different merchants."""
    _, p1_id, _ = _create_merchant_and_products(client)

    # Create second merchant & product
    m2_res = client.post("/api/merchants", json={
        "name": "Merchant 2",
        "business_name": "M2 Ltd",
        "email": f"m2_{uuid.uuid4().hex[:6]}@test.com",
    })
    p3_res = client.post(f"/api/merchants/{m2_res.json()['id']}/products", json={
        "sku": "P3", "name": "Other Merchant Prod", "description": "Desc", "category": "C", "price": 300.00
    })
    p3_id = p3_res.json()["id"]

    res = client.post(f"/api/products/{p1_id}/relationships", json={
        "target_product_id": p3_id,
        "relationship_type": "cross_sell",
        "score": 0.70,
    })
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "BAD_REQUEST"
