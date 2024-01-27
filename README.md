# Billing & Accounting Module

### User Account Credentials

- **Admin User role:**
  - Username: admin_1
  - Password: KMb&2Uq&n99P

- **Team Member User role:**
  - Username: team_member_1
  - Password: qwertyCM12

## Live Demo

- [Billing Demo](https://billing.tahzeebahmed.com)
- [API Access](https://billing.tahzeebahmed.com/api/)

## Screenshots

![Screenshot 1](/demo/screenshots/desktop-dashboard.png)
![Screenshot 2](/demo/screenshots/mobile-dashboard.png)
![Screenshot 3](/demo/screenshots/desktop-dashboard-2.png)
![Screenshot 4](/demo/screenshots/table-view.png)
![Screenshot 5](/demo/screenshots/table-view-2.png)

## Description

This Django-based web application is designed for companies offering event management services, providing a comprehensive accounting and invoice generation system. Tailored for business owners/admins, the platform facilitates client and event management, revenue tracking, and customized Django admin panel features. Additionally, APIs are exposed using Django Rest Framework (DRF) for frontend integration.

## Features

- **User Authentication:**
  - Business owners/admins log in to manage clients, events, and invoices.
  - Employees access personalized dashboards for viewing upcoming events and generating bills.

- **Client and Event Management:**
  - Create and edit client instances.
  - Generate invoices upon event creation, associating events with existing packages and add-ons.

- **Financial Tracking:**
  - Ledgers track revenue from events, packages, and add-ons.
  - Monthly income statements offer consolidated financial data.
  - Admins log customer payments, update payment statuses, and manage cash inflows and outflows.

- **Customized Django Admin Panel:**
  - Admin panel customized for specific process flows, themed with django-admin-volt.

- **API Integration:**
  - APIs exposed using Django Rest Framework (DRF) for frontend integration.

## Installation

To set up the project, follow these steps:

1. Clone the repository.
2. Install dependencies from `requirements.txt`.

## Project Structure
```
< PROJECT ROOT >
   |
   |-- core/
   |    |-- settings/
   |        |-- base.py             # Common Project Configuration
   |        |-- dev.py              # Development Configuration
   |        |-- prod.py             # Production Configuration
   |    |-- urls.py                 # Project Routing
   |
   |-- Billing/                     # Modular Logic for Accounting & Invoice generation
   |    |-- views.py                     # APP Views for bill generation
   |    |-- urls.py                      # APP Routing
   |    |-- models.py                    # APP Models
   |    |-- signals.py                   # Model Signals 
   |    |-- tests.py                     # Tests
   |    |-- templates/                   # Theme Customisation
   |    |-- admin.py                     # Admin Panel Customisation
   |    |-- business_logic/              # Single source of custom validation
   |
   |-- api/
   |    |-- views.py                     # Api Views
   |    |-- urls.py                      # Api Endpoints
   |
   |-- user/                       # Modular Logic for User Management
   |    |-- views.py                     # Api Views
   |    |-- urls.py                      # Api Endpoints
   |
   |-- requirements.txt                  # Project Dependencies
   |
   |-- manage.py                         # Start the app - Django default start script
```



## Usage

1. Run the Django development server.
2. Access the admin panel to explore client, event, and financial management features.
3. Employees log in to view upcoming events and generate bills from their dashboards.

## Documentation

### Business Owner/Admin Functionalities

- **Client Management:**
  - Create and edit client instances.

- **Event Management:**
  - Generate invoices upon event creation.
  - Associate events with existing packages and add-ons.

- **Financial Tracking:**
  - Ledgers track revenue from events, packages, and add-ons.
  - Monthly income statements provide consolidated financial data.
  - Log customer payments, update payment statuses, and manage cash inflows/outflows.

### Employee Functionalities

- **Dashboard:**
  - View upcoming events.

- **Billing:**
  - Generate bills for services provided.
  - Admin manages cost of service and records transactions.

