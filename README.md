# Ecommerce API

A Django REST Framework backend for an ecommerce system with product management, order management, stock tracking, dashboard reports, customer accounts, JWT authentication, and Swagger API documentation.

## Features

* Product and category management
* Product image upload
* Guest order creation
* Authenticated customer order creation
* Saved customer phone and city profile
* Admin order validation, cancellation, and delivery
* Stock movement history
* Manual stock adjustment
* Dashboard statistics
* Revenue reports
* Best-selling products report
* Product search, filtering, and ordering
* JWT authentication
* Swagger API documentation
* Automated test suite

## Tech Stack

* Python
* Django
* Django REST Framework
* SimpleJWT
* drf-spectacular
* django-filter
* django-cors-headers
* python-decouple
* SQLite for development

## API Documentation

Swagger documentation is available at:

```text
http://127.0.0.1:8000/api/docs/
```

API schema endpoint:

```text
http://127.0.0.1:8000/api/schema/
```

## Authentication

The API supports JWT authentication.

### Authentication Endpoints

```text
POST /api/register/
POST /api/token/
POST /api/token/refresh/
```

### Register

```http
POST /api/register/
```

Example request:

```json
{
  "username": "customer1",
  "email": "customer1@example.com",
  "password": "customer12345",
  "password_confirm": "customer12345"
}
```

### Login

```http
POST /api/token/
```

Example request:

```json
{
  "username": "customer1",
  "password": "customer12345"
}
```

Example response:

```json
{
  "refresh": "refresh_token_here",
  "access": "access_token_here"
}
```

### Refresh Access Token

```http
POST /api/token/refresh/
```

Example request:

```json
{
  "refresh": "refresh_token_here"
}
```

### Using JWT

Protected requests should include:

```text
Authorization: Bearer <access_token>
```

## Main API Endpoints

## Products

```text
GET    /api/products/
POST   /api/products/
GET    /api/products/{id}/
PATCH  /api/products/{id}/
DELETE /api/products/{id}/
POST   /api/products/{id}/adjust_stock/
```

Product list supports:

```text
search
category
min_price
max_price
ordering
```

Examples:

```text
/api/products/?search=Mouse
/api/products/?category=1
/api/products/?min_price=30&max_price=100
/api/products/?ordering=price
/api/products/?ordering=-price
/api/products/?ordering=stock
/api/products/?ordering=-stock
/api/products/?ordering=name
/api/products/?ordering=-name
```

### Manual Stock Adjustment

Product stock should not be changed directly from the product detail endpoint.

Use:

```http
POST /api/products/{id}/adjust_stock/
```

Example request:

```json
{
  "quantity_change": 20,
  "note": "New shipment received"
}
```

To decrease stock:

```json
{
  "quantity_change": -5,
  "note": "Damaged items removed"
}
```

This endpoint creates a stock movement history record.

## Categories

```text
GET    /api/categories/
POST   /api/categories/
GET    /api/categories/{id}/
PATCH  /api/categories/{id}/
DELETE /api/categories/{id}/
```

Only admin users can create, update, or delete categories.

Guests and customers can view categories.

## Orders

```text
GET   /api/orders/
POST  /api/orders/
GET   /api/orders/{id}/
POST  /api/orders/{id}/validate_order/
POST  /api/orders/{id}/cancel_order/
POST  /api/orders/{id}/deliver_order/
```

### Order Flow

Allowed status flow:

```text
pending → validated → delivered
pending → cancelled
validated → cancelled
```

Blocked status flow:

```text
pending → delivered
cancelled → delivered
delivered → cancelled
```

### Guest Orders

Guests can create orders by providing:

```text
customer_name
city
phone_number
order_items
```

Example request:

```json
{
  "customer_name": "Test Customer",
  "city": "Berlin",
  "phone_number": "0123456789",
  "notes": "Please call before delivery.",
  "order_items": [
    {
      "product": 1,
      "quantity": 2
    }
  ]
}
```

### Authenticated Customer Orders

Logged-in customers can create orders linked to their account.

Example request:

```json
{
  "city": "Berlin",
  "phone_number": "0123456789",
  "use_saved_phone": false,
  "notes": "First authenticated order.",
  "order_items": [
    {
      "product": 1,
      "quantity": 2
    }
  ]
}
```

Customers can reuse their saved phone and city:

```json
{
  "use_saved_phone": true,
  "notes": "Use my saved contact information.",
  "order_items": [
    {
      "product": 1,
      "quantity": 1
    }
  ]
}
```

## Stock Movements

```text
GET /api/stock-movements/
GET /api/stock-movements/{id}/
```

Stock movements record every stock change.

Examples:

```text
order_created       → stock decreases after order creation
order_cancelled     → stock is restored after order cancellation
manual_adjustment   → admin manually changes stock
```

Filters:

```text
/api/stock-movements/?product=1
/api/stock-movements/?reason=manual_adjustment
/api/stock-movements/?reason=order_created
/api/stock-movements/?reason=order_cancelled
```

Example stock movement response:

```json
{
  "id": 2,
  "product": 2,
  "product_name": "Laptop",
  "order": null,
  "quantity_change": 20,
  "reason": "manual_adjustment",
  "created_at": "2026-06-10T19:04:07.112954Z",
  "note": "New shipment received"
}
```

## Dashboard

```text
GET /api/dashboard/stats/
GET /api/dashboard/low-stock/
GET /api/dashboard/revenue/
GET /api/dashboard/best-sellers/
```

Dashboard endpoints are admin-only.

### Dashboard Stats

```http
GET /api/dashboard/stats/
```

Example response:

```json
{
  "total_orders": 13,
  "pending_orders": 8,
  "validated_orders": 2,
  "delivered_orders": 2,
  "cancelled_orders": 1,
  "total_revenue": 7999.92,
  "low_stock_products": 1
}
```

### Revenue Report

```http
GET /api/dashboard/revenue/
```

Supports date filters:

```text
/api/dashboard/revenue/?start_date=2026-06-01&end_date=2026-06-19
```

### Best-Selling Products

```http
GET /api/dashboard/best-sellers/
```

Supports date filters:

```text
/api/dashboard/best-sellers/?start_date=2026-06-01&end_date=2026-06-19
```

### Low-Stock Products

```http
GET /api/dashboard/low-stock/
```

Returns products with low stock.

## Permissions

### Guests

Guests can:

```text
View products
View categories
Create orders
Register
Login
```

Guests cannot:

```text
Create products
Create categories
View dashboard
View stock movements
Use admin order actions
```

### Customers

Customers can:

```text
Login with JWT
Create orders linked to their account
Reuse saved phone and city
View only their own orders
```

Customers cannot:

```text
View other customers' orders
Validate orders
Cancel orders
Deliver orders
Create products
Create categories
View dashboard
View stock movements
```

### Admin Users

Admin users can:

```text
Manage products
Manage categories
Validate orders
Cancel orders
Deliver orders
Adjust stock
View stock movement history
View dashboard reports
View all orders
```

## Installation

Clone the repository:

```powershell
git clone https://github.com/medali-bay/Ecommerce.git
cd Ecommerce
```

Activate the environment:

```powershell
conda activate django-env
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key
DEBUG=True
```

Run migrations:

```powershell
python manage.py migrate
```

Create a superuser:

```powershell
python manage.py createsuperuser
```

Run the development server:

```powershell
python manage.py runserver
```

Open the API documentation:

```text
http://127.0.0.1:8000/api/docs/
```

## Tests

Run all tests:

```powershell
python manage.py test
```

The test suite covers:

```text
Order creation
Stock decrease and restoration
Order lifecycle
Admin permissions
Customer permissions
Guest validation
Customer profile phone flow
JWT authentication
JWT customer order flow
JWT admin actions
Product filters
Product search
Product ordering
Dashboard reports
Dashboard date filters
Stock movement history
Stock movement filters
Manual stock adjustment
Category permissions
Product image upload
Swagger-safe API behavior
```

## Development Notes

### Stock Management Rule

Product stock should not be changed directly from:

```text
/api/products/{id}/
```

Stock should be changed using:

```text
/api/products/{id}/adjust_stock/
```

This ensures every stock change is recorded in the stock movement history.

### JWT Rule

Use the access token for protected requests:

```text
Authorization: Bearer <access_token>
```

Use the refresh token to get a new access token when needed:

```text
POST /api/token/refresh/
```

### Swagger

Swagger is available at:

```text
/api/docs/
```

The schema is available at:

```text
/api/schema/
```

## Project Status

The backend currently includes:

```text
Core ecommerce API
JWT authentication
Admin workflow
Stock tracking
Dashboard reports
Swagger documentation
Automated test coverage
```

The next possible step is building a frontend for customers and admins.
