def test_get_staff(client):
    """Test GET /staff endpoint."""
    response = client.get('/staff')
    assert response.status_code == 200

def test_get_staff_active_only(client):
    """Test GET /staff?active_only=true endpoint."""
    response = client.get('/staff?active_only=true')
    assert response.status_code == 200

def test_get_staff_member_not_found(client):
    """Test GET /staff/<id> for a non-existent staff member."""
    response = client.get('/staff/99999')
    assert response.status_code == 404

def test_create_staff_bad_request(client):
    """Test POST /staff with no data."""
    response = client.post('/staff', json={})
    assert response.status_code == 400