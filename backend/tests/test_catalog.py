import uuid


def test_ai_catalog_and_search(client):
    """Test AI-readable catalog endpoint and deterministic search endpoint."""
    m_res = client.post("/api/merchants", json={
        "name": "AI Catalog Store",
        "business_name": "AI Store Ltd",
        "email": f"aicatalog_{uuid.uuid4().hex[:6]}@test.com",
    })
    m_id = m_res.json()["id"]

    # Add products
    p1 = client.post(f"/api/merchants/{m_id}/products", json={
        "sku": "KB-01", "name": "Mechanical Keyboard", "description": "RGB Keyboard", "category": "Keyboards", "price": 2500.00, "initial_quantity": 30
    }).json()

    p2 = client.post(f"/api/merchants/{m_id}/products", json={
        "sku": "MS-01", "name": "Wireless Mouse", "description": "Silent Mouse", "category": "Mice", "price": 800.00, "initial_quantity": 0
    }).json()

    # Add relationship KB-01 -> MS-01
    client.post(f"/api/products/{p1['id']}/relationships", json={
        "target_product_id": p2["id"],
        "relationship_type": "cross_sell",
        "score": 0.90,
    })

    # Test GET /api/agent/catalog/{merchant_id}
    cat_res = client.get(f"/api/agent/catalog/{m_id}")
    assert cat_res.status_code == 200
    data = cat_res.json()
    assert data["merchant"]["name"] == "AI Catalog Store"
    assert data["total_count"] == 2

    # Check product structured payload
    item1 = next(item for item in data["products"] if item["sku"] == "KB-01")
    assert item1["availability"]["in_stock"] is True
    assert item1["availability"]["available_quantity"] == 30
    assert item1["commerce_attributes"]["can_cross_sell"] is True
    assert len(item1["related_products"]) == 1
    assert item1["related_products"][0]["sku"] == "MS-01"

    # Test GET /api/agent/catalog/{merchant_id}/search?q=keyboard
    search_res = client.get(f"/api/agent/catalog/{m_id}/search?q=keyboard")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total_count"] == 1
    assert search_data["products"][0]["sku"] == "KB-01"

    # Test in_stock filter search
    stock_res = client.get(f"/api/agent/catalog/{m_id}/search?in_stock=true")
    assert stock_res.status_code == 200
    assert stock_res.json()["total_count"] == 1
    assert stock_res.json()["products"][0]["sku"] == "KB-01"
