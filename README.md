# Electronics Store Inventory Management System (ESIMS)

A Software Engineering Level-3 mini-project (Team 8) to digitize inventory tracking, purchasing, sales and low-stock alerting for a retail electronics store.

## Problem Statement
Electronics stores manage large numbers of SKUs across categories (mobiles, accessories, appliances, components) and struggle to track stock manually — leading to overselling, stockouts, delayed reordering, and poor visibility into fast-moving products. ESIMS digitizes stock tracking, purchase/sales recording, and low-stock alerting for store staff and administrators.

## Team (Group 8)
- Samiksha B N – PES1UG24CS413
- Roopa Sreedhar A – PES1UG24CS386
- Rishitth G R – PES1UG24CS376
- Sakthevel Saravanan – PES1UG24CS405

## Key Features
- Staff / Administrator authentication with role-based access
- Product & category catalog management (CRUD)
- Stock-in (purchase entry) and stock-out (sales entry) workflows with audit trail
- Configurable low-stock threshold alerts
- Supplier management
- Inventory & sales reporting (stock value, top-selling items, low-stock list)
- Search & filter across the product catalog

## Tech Stack
| Layer | Tool |
|---|---|
| Backend | Python (Django) |
| Database | PostgreSQL |
| Frontend | Django Templates + Bootstrap |
| Version Control | Git + GitHub |
| Agile Tracking | GitHub Projects |
| Testing | Django TestCase |
| CI/CD | GitHub Actions |
| Design/UML | Draw.io |

## Architecture
ESIMS is a self-contained, single Django web application (not integrated with any external e-commerce/payment platform), with a relational database and two internal user roles: **Staff** and **Administrator**. It's deployed on a Linux server and accessed via a modern browser (Chrome/Edge/Firefox) — no native mobile app in v1.0.

## Development Approach
Built incrementally using Agile practices — feature-by-feature (authentication, catalog, stock-in/out, suppliers & reporting) across sprints, each producing a working, demoable module. This surfaces integration issues early and allows reporting/alerting rules to be refined as the system is built.

## Repository Contents
- `ESIMS_Synopsis.docx` – Project synopsis (problem statement, tool stack, objectives, scope, functional features, Agile justification)
- `ESIMS_SRS_Team_8.docx` – Full Software Requirements Specification (interfaces, use cases, system features by module, non-functional requirements, traceability matrix)

## Constraints
- Passwords are hashed; plaintext credential storage is not permitted
- Single physical store location (no multi-branch transfers in v1.0)
- No public self-registration — accounts are created internally by an Administrator
- All client-server communication over HTTPS
