# Quick Start Guide

Welcome to StreamlineVPN! This guide will get you up and running in minutes.

## 1. Installation

First, make sure you have Python 3.10+ installed. Then, open your terminal and run the following commands:

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Basic Usage

To run the pipeline and generate the VPN configurations, use the following command:

```bash
python -m streamline_vpn --config config/sources.yaml --output output
```

This will create an `output` directory with the following files:

- `vpn_data.json`: A JSON file containing all the VPN configurations.
- `clash.yaml`: A configuration file for the Clash client.
- `singbox.json`: A configuration file for the Sing-box client.

## 3. Using the API

StreamlineVPN also provides a FastAPI-powered API for more advanced use cases. To start the API server, run:

```bash
python run_server.py
```

The API will be available at `http://localhost:8080`. You can find the full API documentation at `http://localhost:8080/docs`.

## 4. What's Next?

Now that you have a basic understanding of how to use StreamlineVPN, here are some resources to help you dive deeper:

<div class="grid" style="margin-top: 2rem;">
  <div class="card">
    <h3><a href="configuration/">Configuration</a></h3>
    <p>Learn how to customize the behavior of StreamlineVPN with your own configuration files.</p>
  </div>
  <div class="card">
    <h3><a href="api/">API Guide</a></h3>
    <p>Explore the full capabilities of the StreamlineVPN API and learn how to integrate it with your own applications.</p>
  </div>
  <div class="card">
    <h3><a href="DEVELOPMENT.html">Development</a></h3>
    <p>Get involved with the development of StreamlineVPN and learn how to contribute to the project.</p>
  </div>
</div>