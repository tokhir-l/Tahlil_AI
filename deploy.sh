#!/bin/bash
# Tahlil Platform Deployment Script
# Run this on your server to set up the platform

set -e  # Exit on error

echo "=========================================="
echo "  Tahlil Platform Deployment Script"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "⚠️  Please don't run as root. Use a regular user with sudo."
   exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+
echo "🐍 Installing Python 3.11..."
sudo apt install -y python3.11 python3.11-venv python3-pip python3.11-dev

# Install system dependencies
echo "📚 Installing system libraries..."
sudo apt install -y build-essential libssl-dev libffi-dev libpq-dev git curl wget

# Install R (optional - for R integration)
read -p "Install R? (y/n): " install_r
if [ "$install_r" = "y" ]; then
    echo "📊 Installing R..."
    sudo apt install -y r-base r-base-dev
    echo "✅ R installed: $(R --version)"
fi

# Install Julia (optional - for Julia integration)
read -p "Install Julia? (y/n): " install_julia
if [ "$install_julia" = "y" ]; then
    echo "🔬 Installing Julia..."
    JULIA_VERSION="1.9.3"
    wget -q https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-${JULIA_VERSION}-linux-x86_64.tar.gz
    tar -xzf julia-${JULIA_VERSION}-linux-x86_64.tar.gz
    sudo mv julia-${JULIA_VERSION} /opt/julia
    sudo ln -sf /opt/julia/bin/julia /usr/local/bin/julia
    rm julia-${JULIA_VERSION}-linux-x86_64.tar.gz
    echo "✅ Julia installed: $(julia --version)"
fi

# Create application directory
APP_DIR="/opt/tahlil"
echo "📁 Creating application directory at $APP_DIR..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Clone or copy application
if [ -d ".git" ]; then
    echo "📥 Copying application files..."
    cp -r . $APP_DIR/
else
    echo "⚠️  Not a git repository. Please copy files manually to $APP_DIR"
fi

cd $APP_DIR

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Pre-install large packages (optional but recommended)
read -p "Pre-install large packages (torch, transformers)? (y/n): " pre_install
if [ "$pre_install" = "y" ]; then
    echo "📦 Pre-installing large packages..."
    pip install torch transformers spacy langchain
    python -m spacy download en_core_web_sm || true
fi

# Create required directories
echo "📁 Creating directories..."
mkdir -p data runs frontend/dist

# Setup environment variables
if [ ! -f .env ]; then
    echo "⚙️  Setting up environment variables..."
    read -p "Enter GEMINI_API_KEY: " gemini_key
    echo "GEMINI_API_KEY=$gemini_key" > .env
    echo "FLASK_ENV=production" >> .env
    echo "✅ Environment variables saved to .env"
fi

# Install Gunicorn
echo "🚀 Installing Gunicorn..."
pip install gunicorn

# Create systemd service
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/tahlil.service > /dev/null <<EOF
[Unit]
Description=Tahlil Web Application
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "▶️  Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable tahlil
sudo systemctl start tahlil

# Check status
sleep 2
if sudo systemctl is-active --quiet tahlil; then
    echo "✅ Service started successfully!"
    sudo systemctl status tahlil --no-pager
else
    echo "❌ Service failed to start. Check logs: sudo journalctl -u tahlil"
    exit 1
fi

# Install Nginx (optional)
read -p "Install Nginx reverse proxy? (y/n): " install_nginx
if [ "$install_nginx" = "y" ]; then
    echo "🌐 Installing Nginx..."
    sudo apt install -y nginx
    
    read -p "Enter your domain name: " domain_name
    
    sudo tee /etc/nginx/sites-available/tahlil > /dev/null <<EOF
server {
    listen 80;
    server_name $domain_name www.$domain_name;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    sudo ln -sf /etc/nginx/sites-available/tahlil /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo systemctl reload nginx
    
    echo "✅ Nginx configured!"
    
    # Setup SSL
    read -p "Setup SSL with Let's Encrypt? (y/n): " setup_ssl
    if [ "$setup_ssl" = "y" ]; then
        echo "🔒 Setting up SSL..."
        sudo apt install -y certbot python3-certbot-nginx
        sudo certbot --nginx -d $domain_name -d www.$domain_name --non-interactive --agree-tos --email admin@$domain_name || true
        echo "✅ SSL configured!"
    fi
fi

# Configure firewall
read -p "Configure firewall (UFW)? (y/n): " setup_firewall
if [ "$setup_firewall" = "y" ]; then
    echo "🔥 Configuring firewall..."
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
    echo "✅ Firewall configured!"
fi

echo ""
echo "=========================================="
echo "  ✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Application directory: $APP_DIR"
echo "Service status: sudo systemctl status tahlil"
echo "View logs: sudo journalctl -u tahlil -f"
echo "Restart: sudo systemctl restart tahlil"
echo ""
echo "Next steps:"
echo "1. Update DNS to point to this server's IP"
echo "2. Test the application: http://$(hostname -I | awk '{print $1}'):5000"
echo "3. If using Nginx: http://$domain_name"
echo ""
