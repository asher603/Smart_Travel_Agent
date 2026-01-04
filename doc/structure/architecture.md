# Smart Travel Agent - System Architecture & Developer Guide

## 1. Project Overview

**Smart Travel Agent** is an AI-powered travel planning application. It uses a **Microservices Architecture** on the backend and a **Modular MVP (Model-View-Presenter)** architecture on the frontend (PySide6).

The system allows users to register, log in, generate personalized travel itineraries using AI, view their trip history, and manage trip details.

---

## 2. Filesystem Tree & Functionality

```text
Smart_Travel_Agent/
├── client/                                 # Desktop Application (PySide6)
│   ├── assets/
│   │   └── styles.qss                      # Global CSS-like styling for Qt widgets
│   ├── components/                         # Reusable Custom UI Components
│   │   ├── floating_particle.py            # Background animation particles
│   │   ├── modern_input.py                 # Styled QLineEdit with icons/validation
│   │   ├── scale_button.py                 # Buttons with tactile animation
│   │   └── tab_button.py                   # Toggle buttons (e.g., Login/Signup)
│   ├── core/                               # Infrastructure Code
│   │   ├── api.py                          # HTTP Client (Requests) for Gateway communication
│   │   ├── components.py                   # (Legacy/Shared) Component definitions
│   │   ├── event_bus.py                    # Pub/Sub system for module decoupling
│   │   └── shell.py                        # Main Window container (QStackedWidget)
│   ├── modules/                            # Functional Micro-frontends
│   │   ├── auth/                           # Login & Registration
│   │   │   ├── presenter.py                # Handles login logic & token storage
│   │   │   └── view.py                     # Login UI (Split screen, particles)
│   │   ├── dashboard/                      # Main Menu / Navigation Hub
│   │   │   ├── model.py
│   │   │   ├── presenter.py
│   │   │   └── view.py
│   │   ├── history/                        # List of past trips
│   │   │   ├── model.py                    # Fetches history list from API
│   │   │   ├── presenter.py                # Formatting data for the view
│   │   │   └── view.py                     # QListWidget with custom item rows
│   │   ├── trip_form/                      # "Generate Trip" Input Screen
│   │   │   ├── model.py                    # Stores form state
│   │   │   ├── presenter.py                # Validates input & calls Generate API
│   │   │   └── view.py                     # DatePickers, Dropdowns, Inputs
│   │   └── trip_viewer/                    # Itinerary Details View
│   │       ├── model.py
│   │       ├── presenter.py
│   │       └── view.py
│   └── main.py                             # Application Entry Point & Wiring
│
├── gateway_service/                        # API Gateway (FastAPI)
│   ├── main.py                             # Reverse Proxy logic (Forwards /auth, /trips)
│   └── Dockerfile                          # Gateway container config
│
├── server/                                 # Application Server (Business Logic)
│   ├── controllers/                        # Route Handlers
│   │   ├── auth_controller.py              # Login/Register endpoints
│   │   └── trip_controller.py              # History, Generate, Delete endpoints
│   ├── core/
│   │   └── config.py                       # Env vars & App settings
│   ├── models/                             # Pydantic Schemas
│   │   └── requests.py                     # Request/Response models
│   ├── services/                           # Business Logic Layer
│   │   └── auth_service.py                 # User authentication logic
│   └── main.py                             # Server Entry Point (FastAPI)
│
├── ai_service/                             # AI Microservice (LLM Integration)
│   └── (Internal logic for LLM generation)
│
├── data_service/                           # Data Persistence Microservice
│   └── (Internal logic for MongoDB/SQL)
│
└── docker-compose.yml                      # Container Orchestration

```

---

## 3. Design Patterns Implementation

### A. Frontend: Model-View-Presenter (MVP)

The client is strictly divided to ensure separation of concerns.

* **View (`view.py`):** Passive Interface. It defines the UI elements and layout. It **never** contains business logic. It emits `Signals` (e.g., `login_clicked`) when the user interacts.
* **Presenter (`presenter.py`):** The Brain. It subscribes to View signals, processes logic (e.g., input validation), calls the `Service` layer, and updates the View. It **never** touches UI widgets directly; it calls methods on the View interface.
* **Model (`model.py`):** Data Structure. It represents the state of the module and handles raw data transformation.

### B. Frontend: Event Bus (Publisher/Subscriber)

To prevent tight coupling between modules (e.g., Auth needing to import Dashboard), we use a global `EventBus`.

* **Usage:** When a user logs in, the Auth module publishes `login_success`.
* **Reaction:** The `main.py` (Shell) or other modules subscribe to this event and trigger navigation (`shell.switch_to(index)`).
* **Benefit:** Modules remain independent and can be tested in isolation.

### C. Frontend: Shell Architecture (Micro-frontends)

The `Shell` (`core/shell.py`) is the main container window. It manages a `QStackedWidget`. Individual functional areas (Auth, History, TripForm) are developed as isolated "Modules" and registered into the Shell at startup in `main.py`.

### D. Backend: API Gateway Pattern

The Client **only** communicates with the `Gateway Service` (port 8000).

* The Gateway acts as a reverse proxy.
* Requests to `/auth/*` or `/trips/*` are forwarded to the `App Server`.
* Requests to `/ai/*` (if exposed) are forwarded to the `AI Service`.
* **Benefit:** The client does not need to know the internal IP/Port of every microservice.

---

## 4. Key Sub-Systems & Notes

### Navigation Logic

Navigation is handled via the `EventBus` using the `Maps` event.

* **Payload:** `{"index": <int>}`
* **Indices:**
* `0`: Auth (Login/Register)
* `1`: Dashboard (Menu)
* `2`: History (Trip List)
* `3`: Trip Form (Create New)
* `4`: Trip Viewer (Details)



### Data Flow for Trip Generation

1. **Client:** User submits form -> `TripFormPresenter` calls `APIService.post("/trips/generate")`.
2. **Gateway:** Receives request -> Forwards to `App Server`.
3. **App Server:** `trip_controller.py` receives request.
* Calls `AI Service` to generate text.
* Calls `Data Service` to save the event/trip.
* Returns JSON to Gateway.


4. **Client:** `TripFormPresenter` receives JSON -> Publishes `LOAD_TRIP` event -> Navigates to `TripViewer`.

### UI Styling (QSS)

The application uses a hybrid styling approach:

* **Global:** `assets/styles.qss` for generic widget styling.
* **Local:** Specific styling (e.g., modern input borders, shadows, gradients) is injected directly in Python classes (`view.py`) to handle complex states like focus highlights and dynamic colors.

---

## 5. Deployment & Running

### Prerequisites

* Docker & Docker Compose
* Python 3.10+ (for Client)

### Backend (Docker)

```bash
# From root directory
docker-compose up --build -d

```

* Gateway runs on: `http://localhost:8000`

### Client (Local Python)

```bash
# From client directory
pip install -r requirements.txt  # Ensure PySide6, requests are installed
python main.py

```