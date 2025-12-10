# SwarmOS Frontend

Vue 3 + Vite frontend for SwarmOS.

## Development

```bash
# Install dependencies
npm install

# Start dev server (runs on http://localhost:3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Tech Stack

- **Vue 3** - Progressive JavaScript framework
- **Vite** - Next generation frontend tooling
- **Vue Router** - Official router for Vue.js
- **Axios** - HTTP client
- **Tailwind CSS** - Utility-first CSS framework

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable Vue components
│   ├── pages/          # Page components
│   ├── services/       # API client
│   ├── App.vue         # Root component
│   ├── main.js         # Entry point
│   └── style.css       # Global styles
├── index.html          # HTML template
├── vite.config.js      # Vite configuration
└── tailwind.config.js  # Tailwind configuration
```

## Design System

The UI follows a minimal, clean design with:
- Dark mode as default
- Subtle colors and generous whitespace
- Smooth transitions and animations
- Responsive layout

