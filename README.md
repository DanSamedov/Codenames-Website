diff --git a//dev/null b/README.md
index 0000000000000000000000000000000000000000..061dfb65167d390790aafa430f50edeed160bb7b 100644
--- a//dev/null
+++ b/README.md
@@ -0,0 +1,64 @@
+# Codenames Website
+
+An online adaptation of the Codenames board game built to demonstrate full‑stack web development skills.
+The project combines a Django backend, real‑time WebSocket communication, a Tailwind powered frontend and a Docker based deployment pipeline.
+
+**Live site:** [https://codenames.samedov.org](https://codenames.samedov.org)
+
+## Features
+- Multiplayer rooms with team management and score tracking stored in MySQL
+- Real‑time gameplay over WebSockets using Django Channels and Redis
+- Tailwind CSS for the frontend assets
+- Production setup with Nginx handling HTTPS and WebSocket proxying
+- Fully containerised for development and production via Docker Compose
+
+## Tech Stack
+- **Backend:** Django, Django Channels
+- **Frontend:** Tailwind CSS, Django templates
+- **Database:** MySQL
+- **Cache/Broker:** Redis
+- **Deployment:** Docker, Docker Compose, Nginx, Certbot
+
+## Project Structure
+```
+Codenames-Website/
+├── codenames_app/       # Django project source code
+├── docker-compose.prod.yml
+├── nginx/               # Nginx configuration for production
+└── redis/               # Redis configuration
+```
+
+## Local Development
+1. Install [Docker](https://docs.docker.com/get-docker/) and Docker Compose.
+2. Create a `.env.dev` file in the project root with at least:
+   ```env
+   SECRET_KEY=your_dev_secret_key
+   DEBUG=1
+   MYSQL_DATABASE=codenames_database
+   MYSQL_USER=codenames_admin
+   MYSQL_PASSWORD=codenames_admin
+   MYSQL_ROOT_PASSWORD=codenames_root
+   ```
+3. Start the development stack:
+   ```bash
+   docker compose -f codenames_app/docker-compose.dev.yml up --build
+   ```
+4. Visit `http://localhost:8000` to use the app.
+
+## Running Tests
+Set the appropriate environment variables (as in `.env.dev`) and run:
+```bash
+DJANGO_SETTINGS_MODULE=codenames.settings.dev python manage.py test
+```
+
+## Production Deployment
+1. Create a `.env.prod` file with production secrets and database credentials.
+2. Build and run the production stack:
+   ```bash
+   docker compose -f docker-compose.prod.yml up -d --build
+   ```
+3. Nginx terminates TLS and proxies both HTTP and WebSocket traffic to the Django ASGI application.
+
+## License
+This project is provided as‑is without an explicit license. Contact the author if you would like to reuse the code.
+
