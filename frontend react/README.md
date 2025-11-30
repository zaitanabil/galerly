# Galerly React Frontend

Modern React frontend for Galerly - the photography gallery platform designed for artists.

## Migration from HTML to React

This React application is a complete rewrite of the original HTML/JS frontend, following modern React patterns and best practices:

- **Component-based architecture** - Clean, reusable React components
- **TypeScript** - Full type safety throughout the application
- **React Router** - Modern client-side routing
- **Authentication context** - Centralized auth state management
- **GSAP animations** - Smooth, professional animations matching the original design
- **Tailwind CSS** - Utility-first styling with custom design system
- **Lucide React** - Consistent, modern icon set

## Pages Migrated

### Public Pages
- ✅ Home (Landing page with all marketing sections)
- ✅ Login
- ✅ Register
- ✅ Reset Password
- ✅ Contact
- ✅ FAQ
- ✅ Privacy Policy
- ✅ Photographers Directory
- ✅ Individual Portfolio
- ✅ 404 Not Found

### Photographer Dashboard (Protected)
- ✅ Dashboard (Gallery overview)
- ✅ New Gallery
- ✅ Gallery View & Management
- ✅ Profile Settings
- ✅ Billing & Subscription
- ✅ Email Templates

### Client Pages
- ✅ Client Dashboard
- ✅ Client Gallery View (with favorites, comments, downloads)

## Architecture

```
frontend react/
├── src/
│   ├── components/        # Reusable React components
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   ├── Hero.tsx
│   │   ├── ProtectedRoute.tsx
│   │   └── ... (other sections)
│   ├── pages/            # Page components (route targets)
│   │   ├── HomePage.tsx
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   └── ... (other pages)
│   ├── contexts/         # React contexts
│   │   └── AuthContext.tsx
│   ├── utils/           # Utility functions
│   │   └── api.ts       # API wrapper
│   ├── config/          # Configuration
│   │   └── env.ts       # Environment config
│   ├── App.tsx          # Main app component with routes
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles
├── .env                 # Environment variables
├── package.json
├── vite.config.ts
└── tailwind.config.js
```

## Key Features

### Authentication
- JWT-based authentication
- Protected routes with role-based access
- Automatic token refresh
- Persistent login state

### API Integration
- Centralized API utility with interceptors
- Type-safe API calls
- Error handling
- Request timeouts

### Design System
- Glass morphism effects
- Smooth GSAP animations
- Apple-inspired clean aesthetics
- Fully responsive layouts
- Dark mode ready

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run typecheck

# Lint
npm run lint
```

## Environment Variables

Create a `.env` file:

```env
VITE_ENVIRONMENT=local
VITE_IS_LOCALSTACK=true

VITE_BACKEND_HOST=localhost
VITE_BACKEND_PORT=5001
VITE_BACKEND_PROTOCOL=http

VITE_LOCALSTACK_HOST=localhost
VITE_LOCALSTACK_PORT=4566
VITE_S3_RENDITIONS_BUCKET=galerly-renditions-local

# ... (other variables)
```

## Deployment

### Production Build
```bash
npm run build
```

The build output will be in `dist/` directory, ready to deploy to any static hosting service (Vercel, Netlify, S3 + CloudFront, etc.).

### Environment Configuration
For production, update the `.env` file or set environment variables in your hosting platform:
- Set `VITE_IS_LOCALSTACK=false`
- Remove LocalStack-specific variables
- API URLs will auto-configure based on hostname

## Migration Notes

### What Changed
1. **No more HTML files** - Everything is React components
2. **Single Page Application** - Client-side routing with React Router
3. **Type Safety** - Full TypeScript integration
4. **Modern tooling** - Vite for blazing fast builds
5. **Improved state management** - React Context API for auth
6. **Better code organization** - Component-based architecture

### What Stayed the Same
1. **Design language** - Same Apple-inspired aesthetics
2. **Animations** - GSAP animations preserved
3. **User flows** - Same functionality and UX
4. **API contracts** - Compatible with existing backend

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

Proprietary - Galerly Inc.

---

**Note**: This is a clean rewrite. The old HTML/JS frontend in `/frontend` can be archived once this React version is fully deployed and tested.

