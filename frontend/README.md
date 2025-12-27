# Tahlil Frontend

React + TypeScript frontend for the Tahlil AI data analysis platform.

## 🚀 Quick Start

### Development Mode

```bash
cd frontend
npm install
npm run dev
```

Opens at **http://localhost:3000** with hot reload.

> Make sure Flask backend is running: `python app.py` (port 5000)

### Production Build

```bash
npm run build
```

Flask automatically serves from `dist/` folder.

## 📁 Structure

```
frontend/
├── App.tsx                    # Main application
├── components/
│   ├── AuthScreen.tsx         # Login/signup
│   ├── DashboardGallery.tsx   # Dashboard viewer (Superset ready)
│   ├── DataSourceSelector.tsx # Google Sheets import
│   ├── FileManagerModal.tsx   # File management
│   ├── InputArea.tsx          # Chat input
│   ├── LandingPage.tsx        # Welcome page
│   ├── MessageBubble.tsx      # Chat messages
│   ├── SettingsModal.tsx      # Settings
│   └── Sidebar.tsx            # Navigation
├── contexts/
│   └── AuthContext.tsx        # User authentication
├── services/
│   └── api.ts                 # Backend API client
└── types.ts                   # TypeScript definitions
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/data/upload` | POST | Upload files |
| `/api/data/from-link` | POST | Import Google Sheets |
| `/api/run/start` | POST | Start analysis |
| `/api/run/{id}/status` | GET | Get run status |
| `/api/run/{id}/steps` | GET | Get analysis steps |
| `/api/run/{id}/results` | GET | Get final results |
| `/api/run/{id}/cancel` | POST | Cancel run |
| `/api/feedback` | POST | Submit feedback |

## 🎨 Theming

Supports dark/light/system themes via CSS variables.

## 📦 Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
