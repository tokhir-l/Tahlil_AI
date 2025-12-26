# Tahlil Frontend - React + TypeScript

This is the React frontend for Tahlil, built with Vite, TypeScript, and React.

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Development Mode

**Option A: Vite Dev Server (Recommended for frontend development)**
```bash
npm run dev
```
- Runs on http://localhost:3000
- Hot module replacement (HMR)
- Proxies `/api` requests to Flask on port 5000
- Make sure Flask is running separately: `python app.py`

**Option B: Flask Serves React (For full-stack development)**
1. Build React: `npm run build`
2. Run Flask: `python app.py`
3. Access at http://localhost:5000

### 3. Production Build

```bash
npm run build
```

This creates a `dist/` folder that Flask will serve automatically.

## Project Structure

```
frontend/
├── components/          # React components
│   ├── AuthScreen.tsx
│   ├── FileManagerModal.tsx
│   ├── InputArea.tsx
│   ├── LandingPage.tsx
│   ├── MessageBubble.tsx
│   ├── ParticleBackground.tsx
│   ├── SettingsModal.tsx
│   └── Sidebar.tsx
├── contexts/            # React contexts
│   └── AuthContext.tsx
├── services/            # API services
│   ├── api.ts          # Flask API client
│   └── geminiService.ts
├── utils/              # Utility functions
│   └── formatters.ts
├── types.ts            # TypeScript types
├── App.tsx             # Main app component
├── index.tsx           # Entry point
├── index.html          # HTML template
└── vite.config.ts      # Vite configuration
```

## API Integration

The frontend communicates with Flask backend via `/api` endpoints:
- `/api/data/upload` - File uploads
- `/api/run/start` - Start analysis
- `/api/run/{id}/status` - Get run status
- `/api/run/{id}/results` - Get results
- `/api/run/{id}/steps` - Get analysis steps
- `/api/run/{id}/cancel` - Cancel run
- `/api/feedback` - Submit feedback

See `services/api.ts` for all API methods.

## Development Tips

- **Hot Reload**: Changes to React components auto-reload in browser
- **TypeScript**: Type checking with `tsc --noEmit`
- **API Proxy**: Vite proxies `/api/*` to Flask automatically
- **Environment Variables**: Set in `.env` file (see vite.config.ts)

## Building for Production

1. Build React app:
   ```bash
   npm run build
   ```

2. Flask will automatically serve from `frontend/dist/` if it exists

3. For deployment, ensure `frontend/dist/` is included in your deployment package
