# Frontend Implementation Design

## Overview

This document details the implementation approach for the React/TypeScript frontend of the Being-Up-To-Date Assistant application. The frontend provides a user-friendly interface for submitting research queries and displaying results from the backend API.

## Project Structure

```
client/
├── public/
│   ├── favicon.ico
│   └── index.html
├── src/
│   ├── assets/
│   │   └── styles/
│   │       ├── main.css
│   │       └── components.css
│   ├── components/
│   │   ├── Header.tsx
│   │   ├── SearchForm.tsx
│   │   ├── ResultDisplay.tsx
│   │   ├── LoadingSpinner.tsx
│   │   ├── ErrorMessage.tsx
│   │   └── SourceCard.tsx
│   ├── hooks/
│   │   └── useResearch.ts
│   ├── services/
│   │   └── api.ts
│   ├── types/
│   │   └── index.ts
│   ├── utils/
│   │   └── formatters.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── .env
```

## Implementation Steps

### 1. Environment Setup

Create `client/.env` with the following configuration:
```env
VITE_API_URL=http://localhost:8001/api
VITE_MAX_QUERY_LENGTH=500
```

In production, set `VITE_API_URL` to the backend domain with `/api`.

### 2. Dependencies Setup

Create `client/package.json`:
```json
{
  "name": "research-agent-client",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@typescript-eslint/eslint-plugin": "^6.10.0",
    "@typescript-eslint/parser": "^6.10.0",
    "@vitejs/plugin-react": "^4.2.0",
    "eslint": "^8.53.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.4",
    "typescript": "^5.2.2",
    "vite": "^5.0.0"
  }
}
```

### 3. TypeScript Configuration

Create `client/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

Create `client/tsconfig.node.json`:
```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

### 4. Vite Configuration

Create `client/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
```

### 5. Type Definitions

Create `client/src/types/index.ts`:
```typescript
export interface ResearchRequest {
  query: string;
  options?: Record<string, any>;
}

export interface SearchResult {
  id: string;
  title: string;
  url: string;
  snippet: string;
  publishedAt: string;
  source: string;
  relevanceScore: number;
}

export interface Source {
  name: string;
  url: string;
  reliability: string;
  type: string;
}

export interface ResearchStatistics {
  totalResults: number;
  processingTime: number;
  searchTime: number;
  summaryTime: number;
}

export interface ResearchData {
  query: string;
  summary: string;
  results: SearchResult[];
  sources: Source[];
  statistics: ResearchStatistics;
  cached: boolean;
}

export interface ResearchResponse {
  success: boolean;
  data?: ResearchData;
  error?: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}

export interface ApiError {
  message: string;
  code?: string;
  status?: number;
}
```

### 6. API Service

Create `client/src/services/api.ts`:
```typescript
import axios from 'axios';
import { ResearchRequest, ResearchResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add any request processing here
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common error responses
    if (error.response?.status === 429) {
      throw new Error('Too many requests. Please try again later.');
    }
    
    if (error.response?.status >= 500) {
      throw new Error('Server error. Please try again later.');
    }
    
    return Promise.reject(error);
  }
);

export const researchApi = {
  // Submit a research query
  submitResearch: async (request: ResearchRequest): Promise<ResearchResponse> => {
    try {
      const response = await apiClient.post<ResearchResponse>('/api/research', request);
      return response.data;
    } catch (error: any) {
      // Handle network errors
      if (!error.response) {
        throw new Error('Network error. Please check your connection.');
      }
      
      // Return standardized error response
      return {
        success: false,
        error: {
          code: error.response.data?.error?.code || 'UNKNOWN_ERROR',
          message: error.response.data?.error?.message || 'An unexpected error occurred',
          details: error.response.data?.error?.details
        }
      };
    }
  },

  // Health check
  healthCheck: async (): Promise<any> => {
    const response = await apiClient.get('/api/health');
    return response.data;
  }
};
```

### 7. Custom Hooks

Create `client/src/hooks/useResearch.ts`:
```typescript
import { useState, useCallback } from 'react';
import { researchApi } from '../services/api';
import { ResearchRequest, ResearchResponse } from '../types';

export const useResearch = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ResearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submitResearch = useCallback(async (request: ResearchRequest) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await researchApi.submitResearch(request);
      setData(result);
      return result;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to submit research request';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return {
    loading,
    data,
    error,
    submitResearch,
    reset
  };
};
```

### 8. Components

Create `client/src/components/Header.tsx`:
```tsx
import React from 'react';

interface HeaderProps {
  title?: string;
}

const Header: React.FC<HeaderProps> = ({ title = 'Being-Up-To-Date Assistant' }) => {
  return (
    <header className="bg-blue-600 text-white p-4 shadow-md">
      <div className="container mx-auto">
        <h1 className="text-2xl font-bold">{title}</h1>
        <p className="text-blue-100 mt-1">AI-powered research assistant</p>
      </div>
    </header>
  );
};

export default Header;
```

Create `client/src/components/SearchForm.tsx`:
```tsx
import React, { useState, useEffect } from 'react';
import { useResearch } from '../hooks/useResearch';

interface SearchFormProps {
  onSubmit: (query: string) => void;
  loading: boolean;
}

const SearchForm: React.FC<SearchFormProps> = ({ onSubmit, loading }) => {
  const [query, setQuery] = useState('');
  const maxLength = parseInt(import.meta.env.VITE_MAX_QUERY_LENGTH || '500');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim().length >= 3) {
      onSubmit(query);
    }
  };

  const remainingChars = maxLength - query.length;

  return (
    <form onSubmit={handleSubmit} className="mb-8">
      <div className="flex flex-col space-y-4">
        <div className="relative">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your research query..."
            className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none min-h-[120px]"
            disabled={loading}
            maxLength={maxLength}
          />
          <div className={`absolute bottom-2 right-2 text-xs ${remainingChars < 50 ? 'text-red-500' : 'text-gray-500'}`}>
            {remainingChars} characters remaining
          </div>
        </div>
        
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-500">
            Minimum 3 characters required
          </div>
          <button
            type="submit"
            disabled={loading || query.trim().length < 3}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              loading || query.trim().length < 3
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800'
            }`}
          >
            {loading ? 'Researching...' : 'Submit Research'}
          </button>
        </div>
      </div>
    </form>
  );
};

export default SearchForm;
```

Create `client/src/components/LoadingSpinner.tsx`:
```tsx
import React from 'react';

interface LoadingSpinnerProps {
  message?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ message = 'Processing your request...' }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
      <p className="text-gray-600">{message}</p>
    </div>
  );
};

export default LoadingSpinner;
```

Create `client/src/components/ErrorMessage.tsx`:
```tsx
import React from 'react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onRetry }) => {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-red-800">Error</h3>
          <div className="mt-2 text-sm text-red-700">
            <p>{message}</p>
          </div>
          {onRetry && (
            <div className="mt-4">
              <button
                type="button"
                onClick={onRetry}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Retry
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorMessage;
```

Create `client/src/components/SourceCard.tsx`:
```tsx
import React from 'react';
import { Source } from '../types';

interface SourceCardProps {
  source: Source;
}

const SourceCard: React.FC<SourceCardProps> = ({ source }) => {
  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start">
        <div className="flex-shrink-0 mr-3">
          <div className="bg-gray-200 border-2 border-dashed rounded-xl w-16 h-16" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-medium text-gray-900 truncate">{source.name}</h3>
          <p className="text-sm text-gray-500 truncate">{source.url}</p>
          <div className="mt-2 flex items-center text-sm">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              source.reliability === 'high' ? 'bg-green-100 text-green-800' :
              source.reliability === 'medium' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              {source.reliability} reliability
            </span>
            <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {source.type}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SourceCard;
```

Create `client/src/components/ResultDisplay.tsx`:
```tsx
import React from 'react';
import { ResearchData } from '../types';
import SourceCard from './SourceCard';

interface ResultDisplayProps {
  data: ResearchData;
}

const ResultDisplay: React.FC<ResultDisplayProps> = ({ data }) => {
  return (
    <div className="space-y-8">
      {/* Summary Section */}
      <section className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Summary</h2>
        <div className="prose max-w-none">
          <p className="text-gray-700 whitespace-pre-wrap">{data.summary}</p>
        </div>
        <div className="mt-4 text-sm text-gray-500">
          {data.cached && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-2">
              Cached Result
            </span>
          )}
          <span>Processed in {data.statistics.processingTime}ms</span>
        </div>
      </section>

      {/* Results Section */}
      <section>
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          Search Results ({data.statistics.totalResults})
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.results.map((result) => (
            <div key={result.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <h3 className="font-medium text-gray-900 mb-2">{result.title}</h3>
              <p className="text-sm text-gray-600 mb-3">{result.snippet}</p>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">{result.source}</span>
                <a 
                  href={result.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  View Source
                </a>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Sources Section */}
      <section>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Sources</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.sources.map((source, index) => (
            <SourceCard key={index} source={source} />
          ))}
        </div>
      </section>

      {/* Statistics Section */}
      <section className="bg-gray-50 rounded-lg p-4">
        <h3 className="font-medium text-gray-900 mb-2">Research Statistics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{data.statistics.totalResults}</div>
            <div className="text-sm text-gray-500">Results</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{data.statistics.searchTime}ms</div>
            <div className="text-sm text-gray-500">Search Time</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{data.statistics.processingTime}ms</div>
            <div className="text-sm text-gray-500">Total Time</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{Math.round(data.statistics.totalResults > 0 ? (data.statistics.searchTime / data.statistics.totalResults) : 0)}ms</div>
            <div className="text-sm text-gray-500">Avg/Result</div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default ResultDisplay;
```

### 9. Main Application Files

Create `client/src/App.tsx`:
```tsx
import React, { useState } from 'react';
import Header from './components/Header';
import SearchForm from './components/SearchForm';
import ResultDisplay from './components/ResultDisplay';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorMessage from './components/ErrorMessage';
import { useResearch } from './hooks/useResearch';
import { ResearchData } from './types';

const App: React.FC = () => {
  const { loading, data, error, submitResearch, reset } = useResearch();
  const [lastQuery, setLastQuery] = useState<string>('');

  const handleSearch = async (query: string) => {
    setLastQuery(query);
    try {
      await submitResearch({ query });
    } catch (err) {
      // Error is handled by the hook
      console.error('Search failed:', err);
    }
  };

  const handleRetry = () => {
    if (lastQuery) {
      handleSearch(lastQuery);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <SearchForm onSubmit={handleSearch} loading={loading} />
          
          {loading && <LoadingSpinner />}
          
          {error && (
            <ErrorMessage 
              message={error} 
              onRetry={lastQuery ? handleRetry : undefined} 
            />
          )}
          
          {data?.success && data.data && (
            <ResultDisplay data={data.data} />
          )}
          
          {!loading && !error && !data && (
            <div className="text-center py-12">
              <div className="bg-gray-200 border-2 border-dashed rounded-xl w-16 h-16 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-1">Welcome to Being-Up-To-Date Assistant</h3>
              <p className="text-gray-500">Enter a research query above to get started</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default App;
```

Create `client/src/main.tsx`:
```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

Create `client/src/index.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Custom utility classes */
.prose {
  color: #374151;
}

.prose p {
  margin-top: 0;
  margin-bottom: 1rem;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .container {
    padding-left: 1rem;
    padding-right: 1rem;
  }
}
```

### 10. HTML Template

Create `client/index.html`:
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Being-Up-To-Date Assistant - AI-Powered Research Assistant</title>
    <meta name="description" content="AI-powered research assistant that helps you find and summarize information from various sources">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

## Implementation Checklist

- [ ] Create project structure
- [ ] Set up environment configuration
- [ ] Install dependencies with npm
- [ ] Configure TypeScript and Vite
- [ ] Implement type definitions
- [ ] Create API service layer
- [ ] Develop custom hooks
- [ ] Build UI components
- [ ] Implement main application
- [ ] Add styling with Tailwind CSS
- [ ] Test frontend functionality

## Testing the Frontend

1. Install dependencies:
   ```bash
   cd client
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Access the application at `http://localhost:5173`

4. Test the search functionality by entering a query and submitting the form

## Next Steps

1. Implement responsive design
2. Add accessibility features
3. Enhance error handling
4. Add loading states and animations
5. Implement result filtering and sorting
6. Add export functionality for results
7. Write unit tests for components
