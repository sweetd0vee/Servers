# TRS: Apache (httpd)

This image is based on the official `httpd:2.4` image and contains a customized configuration to proxy requests

## Configuration

The `httpd` container is configured using the following environment variables:

* `WEB_PROTOCOL`: Determines the protocol to use (`http` or `https`). This variable loads the corresponding
  configuration file (`proxy-http.conf` or `proxy-https.conf`).
* `SERVER_NAME`: Sets the server name for the virtual host, such as `localhost` or `soundreader.com`.

## Running the Container

### Using Docker Directly

To run the container directly with Docker, you will need to provide SSL certificates for HTTPS support.

#### Demo Certificate (localhost)

For local testing, you can create a self-signed certificate for `localhost`. This certificate will not be trusted by
your browser.

**Generate the Certificate:**

```shell
CERT_DIR="../../.docker/httpd/data/letsencrypt/live/localhost"
mkdir -p "$CERT_DIR"
openssl genrsa -out "$CERT_DIR/privkey.pem" 2048
openssl req -new -x509 -key "$CERT_DIR/privkey.pem" -out "$CERT_DIR/fullchain.pem" -days 3650 -subj "/CN=localhost" -addext "subjectAltName = DNS:localhost,IP:127.0.0.1"
```

**Run the Container with Demo Certificate:**

```shell
docker run -p 80:80 -p 443:443 \
  -e WEB_PROTOCOL=https \
  -e SERVER_NAME=localhost \
  -v ~/.docker-share/httpd/data/letsencrypt/live/localhost:/etc/letsencrypt/live/localhost \
  goolegs/trs/httpd:latest
```

#### Real Certificate (Let's Encrypt)

You can obtain a real SSL certificate from Let's Encrypt using `certbot`.

**Start Container for Certbot Verification (HTTP Mode):**
Run the `httpd` container in HTTP mode and mount a volume to `/usr/local/apache2/htdocs`. `certbot` will use this volume
to verify domain ownership.

```shell
docker run -p 80:80 \
  -e WEB_PROTOCOL=http \
  -e SERVER_NAME=localhost \
  -v ~/docker-share/apache2:/usr/local/apache2/htdocs \
  goolegs/trs/httpd:local
```

**Run Certbot:**
Execute the `certbot` command to get the certificate. The certificate files will be stored in `/etc/letsencrypt`.

```
certbot certonly --webroot -w ~/docker-share/apache2 --noninteractive --agree-tos -d soundreader.com \
--config-dir ~/docker-share/certbot  --work-dir ~/docker-share/certbot --logs-dir ~/docker-share/certbot
```

**Restart Container with Real Certificate (HTTPS Mode):**
Stop the container from the previous step and restart it with `WEB_PROTOCOL=https`, mounting the Let's Encrypt
directory.

```shell
docker run -p 80:80 -p 443:443 \
  -e WEB_PROTOCOL=https \
  -e SERVER_NAME=your.domain.com \
  -v /etc/letsencrypt:/etc/letsencrypt \
  goolegs/trs/httpd:local
  
docker run -p 80:80 -p 443:443 \
  -e WEB_PROTOCOL=https \
  -e SERVER_NAME=localhost \
  -v ~/docker-share/certbot:/etc/letsencrypt \
  goolegs/trs/httpd:local
```

### Using Docker Compose

You can use Docker Compose to manage the `httpd` container, especially for complex setups.

**Docker Compose Example (Demo Certificate):**
Create a `docker-compose.yml` file in your project's root directory with the following content:

```yaml
version: '3.8'

services:
  httpd-proxy:
    image: goolegs/trs/httpd:latest
    container_name: httpd-proxy
    ports:
      - "80:80"
      - "443:443"
    environment:
      - WEB_PROTOCOL=https
      - SERVER_NAME=localhost
    volumes:
      # Mount the directory containing the self-signed certificate
      # This path assumes your docker-compose.yml is at the root of your project
      # and the certificate directory is located at ./.docker/httpd/data/letsencrypt/live/localhost
      - ~/docker-share/httpd/data/letsencrypt/live/localhost:/etc/letsencrypt/live/localhost
    restart: unless-stopped
    # Depending on your setup, you might want to add dependencies here,
    # for example, if this proxy relies on other services like Keycloak or Solr.
    # depends_on:
    #   - keycloak
    #   - solr
```

**How to Use Docker Compose:**

* Ensure you have generated the demo certificate as described in the "Demo Certificate (localhost)" section.
* Save the content above into a file named `docker-compose.yml`.
* Navigate to the directory containing your `docker-compose.yml` file in your terminal.
* Run `docker compose up -d` to start the service in detached mode.
