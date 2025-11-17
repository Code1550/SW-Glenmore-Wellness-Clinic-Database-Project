def test_get_patients(client):
    """Test GET /patients endpoint."""
    response = client.get('/patients')
    assert response.status_code == 200

def test_get_patient_not_found(client):
    """Test GET /patients/<id> for a non-existent patient."""
    response = client.get('/patients/99999')
    assert response.status_code == 404

def test_search_patients_by_name(client):
    """Test GET /patients/search/by-name endpoint."""
    response = client.get('/patients/search/by-name?first_name=Test')
    assert response.status_code == 200

def test_create_patient_bad_request(client):
    """Test POST /patients with no data."""
    response = client.post('/patients', json={})
    # Expecting a 400 Bad Request since data is missing/invalid
    assert response.status_code == 400