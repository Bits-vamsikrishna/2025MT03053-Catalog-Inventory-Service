# OrderHub: Scalable Microservices Architecture & Kubernetes Deployment

> **Course:** Scalable Services  
> **Submission Date:** November 12, 2026  
> **Application Name:** OrderHub  

---

## Executive Summary
**OrderHub** is a cloud-native, microservices-based backend platform designed around Domain-Driven Design (DDD) principles. It handles e-commerce catalog management, inventory tracking, and order processing using isolated microservices. 

Each microservice adheres to the **Database-per-Service** pattern, maintaining its own isolated database instance to prevent domain coupling and performance bottlenecks during high-traffic operations. Inter-service interaction relies on synchronous REST calls over Kubernetes internal DNS services.

---

## System Architecture

### Business Capabilities & Service Mapping

| Service Name | Core Domain | Data Store | Exposed Port | NodePort |
| :--- | :--- | :--- | :--- | :--- |
| `Catalog-Inventory-Service` | Manages products, stock levels, and real-time stock reservations. | `inventory.db` (SQLite) | `8001` | `30001` |
| `Order-Service` | Manages customer orders, stock validation workflows, and order fulfillment states. | `orders.db` (SQLite) | `8002` | `30002` |

---

### Architectural Diagram

```text
+-----------------------------------------------------------------------------------+
|                           EXTERNAL CLIENT / API CONSUMER                          |
|                                (Postman / Browser)                                |
+-----------------------------------------+-----------------------------------------+
                                          |
                  HTTP REST (NodePort 30001 / 30002 or Port-Forward)
                                          |
+-----------------------------------------v-----------------------------------------+
|                         MINIKUBE KUBERNETES CLUSTER                               |
|                                                                                   |
|   +---------------------------------+       +----------------------------------+  |
|   |   K8s Service: order-service    |       | K8s Service: inventory-service   |  |
|   |   (NodePort: 8002 -> 30002)     |       | (ClusterIP/NodePort: 8001->30001)|  |
|   +----------------+----------------+       +----------------+-----------------+  |
|                    |                                         |                    |
|                    v                                         v                    |
|   +---------------------------------+       +---------------------------------+   |
|   |      Order-Service Pod          |       |  Catalog-Inventory-Service Pod  |   |
|   |      (FastAPI / Uvicorn)        |       |       (FastAPI / Uvicorn)       |   |
|   |                                 |       |                                 |   |
|   |  Commands:                      |       |  Commands:                      |   |
|   |   - POST /orders (placeOrder)   +------>+   - PUT /products/{id}/reserve  |   |
|   |                                 | HTTP  |   - POST /products              |   |
|   |  Queries:                       | PUT   |   - DELETE /products/{id}       |   |
|   |   - GET /orders                 | (K8s  |  Queries:                       |   |
|   |   - GET /orders/{id}            | DNS)  |   - GET /products               |   |
|   |                                 |       |   - GET /products/{id}          |   |
|   +----------------+----------------+       +----------------+----------------+   |
|                    |                                         |                    |
|                    v                                         v                    |
|   +---------------------------------+       +---------------------------------+   |
|   |      Orders Database            |       |      Inventory Database         |   |
|   |      (SQLite: orders.db)        |       |      (SQLite: inventory.db)     |   |
|   +---------------------------------+       +---------------------------------+   |
+-----------------------------------------------------------------------------------+
```

---

## Tech Stack & Frameworks

- **Backend Framework:** Python 3.11 with FastAPI
- **ASGI Server:** Uvicorn
- **ORM & Data Layer:** SQLAlchemy 2.0 & Pydantic v2
- **Database:** SQLite 3 (Database-per-service isolation pattern)
- **HTTP Client:** HTTPX (for async/sync HTTP collaboration)
- **Containerization:** Docker (`python:3.11-slim`)
- **Orchestration:** Kubernetes (Minikube driver)

---

## Repository

Note: Both the Services have been uploaded into different GitHub Repositories. PFB GitHub Repo Links:

| Service Name | GitHub URLs | 
| :--- | :--- | 
| `Catalog-Inventory-Service` | (https://github.com/2025mt03081-sudo/Scalable_Services_Assignment-1_Catalog-Inventory-Service) |
| `Order-Service` | (https://github.com/2025mt03081-sudo/Scalable_Services_Assignment-1_Order-Service) |

---

## Project Layout

```text
OrderHub
|
├── 2025MT03053_OrderHub.postman_collection.json
|
├── 2025MT03053_inventory-service-repo/
│   ├── 2025MT03053_app/
│   │   └── main.py            # Inventory FastAPI endpoints & models
│   ├── requirements.txt       # Dependencies
│   ├── Dockerfile             # Container definition (Port 8001)
│   └── k8s-deployment.yaml    # K8s Deployment & NodePort Service specs
│
└── 2025MT03053_order-service-repo/
    ├── 2025MT03053_app/
    │   └── main.py            # Order FastAPI endpoints & inter-service client
    ├── requirements.txt       # Dependencies
    ├── Dockerfile             # Container definition (Port 8002)
    └── k8s-deployment.yaml    # K8s Deployment & NodePort Service specs
```

---

## Step-by-Step Local Deployment Guide

### Prerequisites
- Docker Desktop installed & running
- `kubectl` installed
- `minikube` installed

### 1. Launch Minikube Cluster
```bash
minikube start --driver=docker
```

### 2. Build Docker Container Images
Build the container images directly into Minikube's internal Docker registry:

```bash
# On Linux/macOS:
eval $(minikube -p minikube docker-env)

# On Windows PowerShell:
# minikube -p minikube docker-env --shell powershell | Invoke-Expression

# Build Catalog-Inventory-Service
cd inventory-service-repo
docker build -t inventory-service:v1 .

# Build Order-Service
cd ../order-service-repo
docker build -t order-service:v1 .
```

*Note: Alternatively, if you build images on host Docker, run `minikube image load inventory-service:v1` and `minikube image load order-service:v1`.*

### 3. Deploy Resources to Kubernetes
```bash
kubectl apply -f ../2025MT03053_inventory-service-repo/k8s-deployment.yaml
kubectl apply -f k8s-deployment.yaml
```

### 4. Verify Kubernetes Pods & Services
```bash
kubectl get pods,deployments,svc -o wide
```
Ensure both pods reach `1/1 Running` status.

### 5. Launch Kubernetes Dashboard
```bash
minikube dashboard
```

---

## Postman API Verification Guide

Port-forward the Kubernetes service endpoints to access them locally:

```bash
kubectl port-forward svc/inventory-service 8001:8001 &
kubectl port-forward svc/order-service 8002:8002 &
```

### 1. Create a Product (`POST /products`)
- **URL:** `http://localhost:8001/products`
- **Method:** `POST`
- **Body (`json`):**
  ```json
  {
    "name": "Wireless Mechanical Keyboard",
    "sku": "KB-MECH-01",
    "price": 89.99,
    "stock_qty": 15
  }
  ```
- **Response (`201 Created`):** Returns product object with `"id": 1`.

### 2. Place an Order (`POST /orders`)
- **URL:** `http://localhost:8002/orders`
- **Method:** `POST`
- **Body (`json`):**
  ```json
  {
    "customer_id": "CUST-1001",
    "product_id": 1,
    "quantity": 3
  }
  ```
- **Response (`201 Created`):** Returns order summary showing `"status": "CONFIRMED"` and `"total_price": 269.97`.

### 3. Verify Inventory Stock Deduction (`GET /products/1`)
- **URL:** `http://localhost:8001/products/1`
- **Method:** `GET`
- **Response (`200 OK`):** Shows updated `"stock_qty": 12` (deducted 3 from initial 15).

### 4. Delete a Product (`DELETE /products/{id}`)
- **URL:** `http://localhost:8001/products/1`
- **Method:** `DELETE`
- **Response (`200 OK`):** `"Product 'Wireless Mechanical Keyboard' (ID: 1) deleted successfully."`

---

## Author Details & Submission Info

- **Student Name:** `Vamsikrishna Pandravada`
- **Student ID:** `2025MT03053`
- **Course:** Scalable Services