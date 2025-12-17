# Deploying to Cloudflare

This guide provides instructions for deploying the ZRL Manager application to Cloudflare using Cloudflare Tunnel.

## Prerequisites

*   A Cloudflare account.
*   `cloudflared` CLI installed and authenticated. You can find instructions on how to do this in the [Cloudflare documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/).

## Deployment Steps

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run the application:**
    Start the application using the production server:
    ```bash
    python run.py
    ```
    The application will be running on `http://localhost:5000`.

3.  **Create a Cloudflare Tunnel:**
    Open a new terminal and run the following command to create a Cloudflare Tunnel:
    ```bash
    cloudflared tunnel --url http://localhost:5000
    ```
    This will create a public URL for your application, which you can use to access it from anywhere.

## Notes

*   This deployment method is suitable for development and testing purposes. For a production environment, you should consider a more robust deployment strategy, such as running the application as a service and using a persistent Cloudflare Tunnel.
*   Make sure your MySQL database is accessible from where you are running the application. If you are running the application on a different machine than your database, you will need to update the `SQLALCHEMY_DATABASE_URI` in `newZRL/config.py` to point to the correct database host.
