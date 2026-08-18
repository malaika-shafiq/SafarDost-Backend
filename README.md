# Safardost Backend API Platform ⛰️🚌

Safardost is a comprehensive, production-ready backend engine designed to power modern tourism and itinerary planning platforms across Pakistan. Built using strict architectural designs and synchronous data patterns, the platform integrates live external communication channels with local database caches.

## 📊 Current Project Status: 76% Complete

### 📦 Core Engineering Implementations (100% Finalized)
1. **User Identity Management**: Stateful session tracking engine with built-in Role-Based Access Control (RBAC) security switches.
2. **Discovery Catalog System**: Intelligent discovery searches powered by case-insensitive token filters (`.ilike`).
3. **Polymorphic Review Ecosystem**: Review framework enforcing strict automated date logging constraints.
4. **Unified Booking Engine**: Financial calculation system processing native stay-duration price allocations in PKR.
5. **Automated Notification Layer**: Synchronous `smtplib` auto-alert email triggers for platform transactions.
6. **Smart Weather Synchronization Cache**: Native `urllib` HTTPS gateway to WeatherAPI featuring an active 30-minute cache expiration safety guard and role-protected admin purge endpoints.

### 🚧 Active Branch Feature Layer (In Progress)
* **Intelligent AI Recommendation Engine**: Multi-day trip plan synthesizers connecting Google Gemini AI outputs with internal database constraints, complete with custom budget guardrails and live weather safety overrides.

## 🛠️ Technology Stack
* **Framework**: FastAPI (Strict Synchronous Architecture Pattern)
* **Validation Layer**: Pydantic v2 (Explicit Field-by-Field Payload Layouts)
* **Database Engine**: SQLAlchemy ORM with an optimized SQLite / PostgreSQL-ready storage scheme
* **AI Engine Context**: Google AI Studio (Gemini 1.5 Flash API Network)

## 🚀 How to Run Locally
1. Clone this repository to your machine.
2. Ensure you have your active secrets mapped inside a `.env` file at the root:
   ```env
   WEATHER_API_KEY=your_key
   GOOGLE_GEMINI_KEY=your_key
   ```
3. Start the application reload engine:
   ```bash
   uvicorn main:app --reload
   ```
