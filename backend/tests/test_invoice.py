def test_get_invoices(client):
    """Test GET /invoices endpoint."""
    response = client.get('/invoices')
    assert response.status_code == 200

def test_get_invoice_not_found(client):
    """Test GET /invoices/<id> for a non-existent invoice."""
    response = client.get('/invoices/99999')
    assert response.status_code == 404

def test_get_invoices_by_patient(client):
    """Test GET /invoices/patient/<id> endpoint."""
    response = client.get('/invoices/patient/99999')
    assert response.status_code == 200 # Returns 200 and empty list

def test_get_invoice_lines(client):
    """Test GET /invoices/<id>/lines endpoint."""
    response = client.get('/invoices/99999/lines')
    assert response.status_code == 200 # Returns 200 and empty list

def test_get_payments(client):
    """Test GET /payments endpoint."""
    response = client.get('/payments')
    assert response.status_code == 200

def test_get_payment_not_found(client):
    """Test GET /payments/<id> for a non-existent payment."""
    response = client.get('/payments/99999')
    assert response.status_code == 404

def test_get_payments_by_patient(client):
    """Test GET /payments/patient/<id> endpoint."""
    response = client.get('/payments/patient/99999')
    assert response.status_code == 200 # Returns 200 and empty list

def test_get_payments_by_invoice(client):
    """Test GET /payments/invoice/<id> endpoint."""
    response = client.get('/payments/invoice/99999')
    assert response.status_code == 200 # Returns 200 and empty list