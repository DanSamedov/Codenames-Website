# Codenames Online (Real-Time Multiplayer)

> **Live Demo:** [codenames.samedov.org](https://codenames.samedov.org)

An engineered, full-stack adaptation of the popular board game "Codenames," built to demonstrate scalable real-time communication patterns and production-grade deployment practices.

## Project Overview
This project solves the challenge of synchronizing game state across multiple clients with near-zero latency. Unlike standard HTTP request-response web apps, this application utilizes persistent **WebSocket** connections to push updates to players instantly (e.g., when a Spymaster gives a clue or an Operative reveals a card).

The system supports multiple concurrent game rooms, distinct roles (Spymaster/Operative), and isolated game states, all orchestrated via a containerized backend.

## Technical Architecture

### Core Stack
| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend** | **Django & Python** | Core game logic, ORM, and HTTP routing. |
| **Async Protocol** | **Django Channels (ASGI)** | Handling persistent WebSocket connections for real-time events. |
| **Message Broker** | **Redis** | In-memory backing store for channel layers (speeding up socket communication). |
| **Database** | **MySQL** | Persistent storage for user profiles, game history, and room metadata. |
| **Frontend** | **JavaScript & Tailwind CSS** | Responsive UI with event-driven DOM updates based on socket messages. |

### Infrastructure & DevOps
* **Containerization:** Fully Dockerized services defined via `docker-compose` for consistent environments.
* **Reverse Proxy:** **Nginx** configured as a gateway to handle SSL termination (HTTPS) and route WebSocket traffic (`ws://` -> `wss://`).
* **CI/CD:** Automated workflows (GitHub Actions) for testing and deployment.

## Key Engineering Features

### 1. Real-Time State Synchronization
Instead of polling the server, the application uses **WebSockets**.
* **Event-Driven:** When a player clicks a card, a JSON payload is sent over the socket.
* **Broadcasts:** The backend processes the move, updates the game state in the database, and broadcasts the new board state to *only* the specific room's group via Redis.
* **Latency Handling:** Optimistic UI updates are used in specific scenarios to ensure the game feels "snappy" even on slower connections.

### 2. Room & Team Management
* **Concurrency:** The backend handles multiple game instances simultaneously without data cross-contamination.
* **Role Security:** Spymasters receive a different data payload (showing all card colors) than Operatives (showing only revealed cards), enforced at the server level to prevent cheating via "Inspect Element."

### 3. Production-Ready Deployment
The application is deployed on a Linux VPS using a production-grade configuration:
* **ASGI Interface:** Uses `daphne` or `uvicorn` to serve async content.
* **Static Files:** Offloaded to Nginx for performance.
* **Security:** Enforced HTTPS via Certbot/Let's Encrypt.

## Repository Structure
* `codenames_app/` - Core Django application logic and consumers (WebSocket handlers).
* `codenames/` - Project configuration and ASGI routing.
* `nginx/` - Custom configuration for WebSocket proxying and static serving.
* `docker-compose.prod.yml` - Orchestration for the production environment.

---
*Created by [Dan Samedov](https://github.com/DanSamedov)*
