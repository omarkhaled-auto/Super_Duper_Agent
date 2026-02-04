import express from 'express';
import path from 'path';
import { bookmarkRouter } from './routes';
import { corsMiddleware, requestLogger, errorHandler } from './middleware';

const app = express();

// 1. CORS (must be first for preflight handling)
app.use(corsMiddleware);

// 2. Request logger
app.use(requestLogger);

// 3. JSON body parser
app.use(express.json());

// 4. Static files from public directory
app.use(express.static(path.join(__dirname, '..', 'public')));

// API routes
app.use('/bookmarks', bookmarkRouter);

// Error handler must be last
app.use(errorHandler);

const PORT = process.env.PORT || 3000;

// Only start server if not in test environment
if (process.env.NODE_ENV !== 'test') {
  app.listen(PORT, () => {
    console.log(`LinkVault server running at http://localhost:${PORT}`);
    console.log(`Dashboard: http://localhost:${PORT}/`);
    console.log(`API: http://localhost:${PORT}/bookmarks`);
  });
}

export { app };
