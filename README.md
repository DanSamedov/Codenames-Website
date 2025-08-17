Codenames Website

An online adaptation of the Codenames board game, showcasing full-stack development with real-time multiplayer, a Django backend, and a Tailwind-powered UI.

Live site: https://codenames.samedov.org

🚀 Features

🧩 Multiplayer rooms with team management and score tracking (MySQL).

⚡ Real-time gameplay over WebSockets via Django Channels and Redis.

🎨 Responsive, clean interface styled with Tailwind CSS.

🔐 Production-ready Nginx setup (TLS + WebSocket proxying).

🐳 Fully containerized for development and production using Docker Compose.

🛠 Technologies Used

Backend: Django, Django Channels (ASGI)

Frontend: Tailwind CSS, Django templates

Database: MySQL

Cache/Broker: Redis

Web Server: Nginx (+ Certbot for HTTPS)

Deployment: Docker & Docker Compose

📦 Project Structure
Codenames-Website/
├── codenames_app/ # Django project source code
├── docker-compose.prod.yml
├── nginx/ # Nginx configuration for production
└── redis/ # Redis configuration

📄 License

This project is provided as-is without an explicit license. Contact the author if you would like to reuse the code.

Made with ❤️ by Danylo Samedov
