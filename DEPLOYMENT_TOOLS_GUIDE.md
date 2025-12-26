# Complete Tools & Dependencies List + Online Deployment Guide

## 📦 Complete List of All Tools & Dependencies

### ✅ **Python Packages (Auto-Installed)**

These are **automatically installed** when tools are first accessed. No manual installation needed!

#### **Core Platform Dependencies**
```
google-generativeai>=0.8.0    # Google Gemini AI
pydantic>=2.12.0               # Data validation
PyYAML>=6.0                    # Configuration files
tqdm>=4.67.0                   # Progress bars
requests>=2.32.0               # HTTP requests
openai>=2.8.1                  # OpenAI API
pandas>=2.3.3                  # Data manipulation
openpyxl>=3.1.5                # Excel files
ollama>=0.6.1                  # Ollama models
flask>=3.0.0                   # Web framework
flask-cors>=4.0.0              # CORS support
matplotlib>=3.8.0             # Plotting
numpy>=1.26.0                  # Numerical computing
scipy>=1.12.0                  # Scientific computing
tabulate>=0.9.0                # Table formatting
seaborn>=0.13.0                # Statistical visualization
plotly>=5.18.0                 # Interactive charts
scikit-learn>=1.4.0            # Machine learning
python-dotenv>=1.0.0           # Environment variables
```

#### **Tool Integration Packages (Auto-Installed on First Use)**

**Phase 1 - Easy Integrations:**
```
statsmodels>=0.14.0            # Statistical analysis
sqlalchemy>=2.0.0              # Database connectivity
spacy>=3.7.0                   # NLP processing
transformers>=4.36.0           # Hugging Face models
torch>=2.1.0                   # PyTorch (large ~2GB)
langchain>=0.1.0               # AI workflows
langchain-community>=0.0.1    # LangChain extensions
langchain-google-genai>=0.0.5  # Google AI integration
gspread>=5.12.0                # Google Sheets
google-auth>=2.25.0            # Google authentication
google-auth-oauthlib>=1.2.0    # OAuth support
google-api-python-client>=2.111.0  # Google APIs
```

**Phase 2 - Moderate Integrations:**
```
rpy2>=3.5.0                    # R integration bridge
julia>=0.6.0                   # Julia bridge
pyreadstat>=1.2.0              # SPSS/Stata file reading
pyarrow>=14.0.0                # Parquet support
xlrd>=2.0.0                    # Legacy Excel support
```

**Optional Database Drivers:**
```
psycopg2-binary>=2.9.0         # PostgreSQL (uncomment if needed)
pymysql>=1.1.0                 # MySQL (uncomment if needed)
```

---

### ⚠️ **External Software (Manual Installation Required)**

These **cannot be auto-installed** and must be installed on the server separately:

#### **1. R (for R Integration)**
- **Download:** https://www.r-project.org/
- **Installation:** Follow OS-specific instructions
- **Verification:** `R --version` should work
- **Size:** ~200-300 MB
- **License:** Free (GPL)

#### **2. Julia (for Julia Integration)**
- **Download:** https://julialang.org/downloads/
- **Installation:** Extract and add to PATH
- **Verification:** `julia --version` should work
- **Size:** ~200-500 MB
- **License:** Free (MIT)


---

## 🌐 Making the Platform Available Online

### **Option 1: Cloud VPS (Recommended for Production)**

#### **Step 1: Choose a Provider**

**Best Options:**
- **DigitalOcean** ($6-12/month) - Simple, reliable
- **Linode** ($5-10/month) - Good performance
- **Vultr** ($6-12/month) - Global locations
- **Hetzner** (€4-8/month) - Very cheap (Europe)
- **AWS Lightsail** ($3.50-10/month) - Amazon's simple option

#### **Step 2: Create Server**

1. **Create Droplet/Instance:**
   - OS: Ubuntu 22.04 LTS
   - Size: 2GB RAM minimum (4GB recommended for ML tools)
   - Storage: 40GB minimum (80GB+ for PyTorch/transformers)
   - Region: Choose closest to your users

2. **SSH into Server:**
   ```bash
   ssh root@your-server-ip
   ```

#### **Step 3: Install System Dependencies**

```bash
# Update system
apt update && apt upgrade -y

# Install Python 3.11+
apt install -y python3.11 python3.11-venv python3-pip

# Install system libraries for tools
apt install -y build-essential libssl-dev libffi-dev
apt install -y libpq-dev  # For PostgreSQL support
apt install -y git curl wget

# Install R (if using R integration)
apt install -y r-base r-base-dev

# Install Julia (if using Julia integration)
wget https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-1.9.3-linux-x86_64.tar.gz
tar -xzf julia-1.9.3-linux-x86_64.tar.gz
mv julia-1.9.3 /opt/julia
ln -s /opt/julia/bin/julia /usr/local/bin/julia

# Install MATLAB (if using - requires license)
# Follow MATLAB installation guide for Linux
```

#### **Step 4: Deploy Application**

```bash
# Clone your repository
cd /opt
git clone https://github.com/yourusername/tahlil.git
cd tahlil

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install core dependencies (auto-install will handle tools)
pip install --upgrade pip
pip install -r requirements.txt

# Create required directories
mkdir -p data runs frontend/dist

# Set environment variables
export GEMINI_API_KEY="your-api-key-here"
export FLASK_ENV="production"
export FLASK_APP="app.py"

# Or use .env file
nano .env
# Add: GEMINI_API_KEY=your-key
```

#### **Step 5: Setup Production Server (Gunicorn)**

```bash
# Install Gunicorn
pip install gunicorn

# Create systemd service
sudo nano /etc/systemd/system/tahlil.service
```

**Service file content:**
```ini
[Unit]
Description=Tahlil Web Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/tahlil
Environment="PATH=/opt/tahlil/venv/bin"
Environment="GEMINI_API_KEY=your-api-key"
ExecStart=/opt/tahlil/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable tahlil
sudo systemctl start tahlil
sudo systemctl status tahlil
```

#### **Step 6: Setup Nginx Reverse Proxy**

```bash
# Install Nginx
apt install -y nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/tahlil
```

**Nginx config:**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files
    location /static {
        alias /opt/tahlil/frontend/dist;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/tahlil /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### **Step 7: Setup SSL (HTTPS)**

```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (already configured)
sudo certbot renew --dry-run
```

#### **Step 8: Configure Firewall**

```bash
# Allow HTTP, HTTPS, SSH
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

#### **Step 9: DNS Configuration (GoDaddy)**

1. **Login to GoDaddy** → My Products → DNS Management
2. **Add A Records:**
   ```
   Type: A
   Name: @
   Value: [Your server IP]
   TTL: 600
   
   Type: A
   Name: www
   Value: [Your server IP]
   TTL: 600
   ```
3. **Wait 5 minutes to 48 hours** for DNS propagation

---

### **Option 2: Platform-as-a-Service (Easiest)**

#### **Railway (Recommended)**

1. **Sign up:** https://railway.app
2. **Connect GitHub** repository
3. **Create new project** → Deploy from GitHub
4. **Add environment variables:**
   - `GEMINI_API_KEY=your-key`
   - `FLASK_ENV=production`
5. **Deploy** - Railway auto-detects Flask
6. **Add custom domain** in Railway settings
7. **Update DNS** in GoDaddy to Railway's provided IP

**Pros:**
- ✅ Automatic deployments
- ✅ Built-in SSL
- ✅ Easy scaling
- ✅ No server management

**Cons:**
- ❌ More expensive ($5-20/month)
- ❌ Less control
- ❌ May need to install external software manually

#### **Render**

1. **Sign up:** https://render.com
2. **New Web Service** → Connect GitHub
3. **Configure:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. **Add environment variables**
5. **Deploy**

#### **Fly.io**

1. **Install Fly CLI:** `curl -L https://fly.io/install.sh | sh`
2. **Login:** `fly auth login`
3. **Deploy:** `fly launch`
4. **Add domain:** `fly domains add yourdomain.com`

---

### **Option 3: Docker Deployment (Advanced)**

#### **Create Dockerfile**

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install R (optional)
RUN apt-get update && apt-get install -y r-base r-base-dev || true

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p data runs frontend/dist

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:5000", "app:app"]
```

#### **Deploy to Docker Hosting**

- **Docker Hub** + Any VPS
- **AWS ECS**
- **Google Cloud Run**
- **Azure Container Instances**

---

## 🔧 **Pre-Installation Strategy for Online Deployment**

### **Recommended: Pre-Install Large Packages**

For faster startup and better user experience, pre-install large packages:

```bash
# On your server, before deployment
source venv/bin/activate

# Pre-install large packages
pip install torch transformers spacy langchain

# Download spaCy models
python -m spacy download en_core_web_sm

# Pre-install all tool packages
pip install statsmodels sqlalchemy gspread rpy2 julia splunk-sdk saspy pyreadstat
```

### **Create Startup Script**

```bash
#!/bin/bash
# /opt/tahlil/start.sh

source /opt/tahlil/venv/bin/activate
cd /opt/tahlil

# Pre-check and install any missing packages
python -c "from tools.base import register_default_tools; register_default_tools()"

# Start server
gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
```

---

## 📊 **Resource Requirements**

### **Minimum Server Specs**

**For Basic Usage:**
- CPU: 2 cores
- RAM: 2GB
- Storage: 40GB
- Cost: $5-10/month

**For Full Features (All Tools):**
- CPU: 4 cores
- RAM: 8GB (PyTorch needs ~4GB)
- Storage: 100GB (for models and data)
- Cost: $20-40/month

**For Enterprise:**
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 200GB+
- Cost: $50-100/month

### **Storage Breakdown**

- **PyTorch:** ~2GB
- **Transformers models:** ~5-10GB (if downloading)
- **spaCy models:** ~500MB
- **Application:** ~500MB
- **Data storage:** Varies
- **Total:** ~10-15GB minimum

---

## 🔐 **Security Checklist for Online Deployment**

1. ✅ **Use HTTPS** (SSL certificate)
2. ✅ **Set strong API keys** (environment variables)
3. ✅ **Enable firewall** (only ports 80, 443, 22)
4. ✅ **Use non-root user** for application
5. ✅ **Regular updates** (`apt update && apt upgrade`)
6. ✅ **Backup strategy** (database, files)
7. ✅ **Monitor logs** (check for errors)
8. ✅ **Rate limiting** (prevent abuse)
9. ✅ **Input validation** (prevent injection)
10. ✅ **CORS configuration** (restrict origins)

---

## 🚀 **Quick Start: Deploy in 30 Minutes**

### **Using Railway (Easiest)**

1. **Push code to GitHub**
2. **Sign up at Railway.app**
3. **New Project** → Deploy from GitHub
4. **Add environment variable:** `GEMINI_API_KEY`
5. **Deploy** → Get URL
6. **Add custom domain** in Railway
7. **Update GoDaddy DNS** to Railway IP
8. **Done!** 🎉

### **Using DigitalOcean (More Control)**

1. **Create Droplet** (Ubuntu 22.04, 4GB RAM)
2. **SSH into server**
3. **Run setup script:**
   ```bash
   git clone https://github.com/yourusername/tahlil.git
   cd tahlil
   bash deploy.sh  # Create this script
   ```
4. **Configure Nginx + SSL**
5. **Update DNS**
6. **Done!** 🎉

---

## 📝 **Deployment Checklist**

- [ ] Server/VPS provisioned
- [ ] Python 3.11+ installed
- [ ] Application code deployed
- [ ] Virtual environment created
- [ ] Core dependencies installed
- [ ] Environment variables set
- [ ] Gunicorn configured
- [ ] Nginx reverse proxy setup
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] DNS configured
- [ ] External software installed (R, Julia, etc. if needed)
- [ ] Monitoring setup
- [ ] Backup strategy in place
- [ ] Domain connected
- [ ] HTTPS working
- [ ] Test all features

---

## 🆘 **Troubleshooting**

### **Port Already in Use**
```bash
# Find process
lsof -i :5000
# Kill process
kill -9 <PID>
```

### **Package Installation Fails**
```bash
# Update pip
pip install --upgrade pip
# Install with verbose output
pip install -v package-name
```

### **External Software Not Found**
- Ensure software is in PATH
- Check installation: `which R`, `which julia`
- Restart server after installation

### **SSL Certificate Issues**
```bash
# Check certificate
certbot certificates
# Renew manually
certbot renew
```

---

## 📞 **Support**

For deployment issues:
1. Check server logs: `journalctl -u tahlil -f`
2. Check Nginx logs: `tail -f /var/log/nginx/error.log`
3. Verify environment variables
4. Test locally first

---

*Deployment Guide - December 2025*  
*Tahlil Platform*
