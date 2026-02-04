import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import bookmarkRoutes from './routes/bookmarks.js';
import collectionRoutes from './routes/collections.js';
import tagRoutes from './routes/tags.js';
import searchRoutes from './routes/search.js';
import { errorHandler } from './middleware/errorHandler.js';

const app = express();
const PORT = process.env.PORT || 3000;

// Global middleware
app.use(cors());
app.use(morgan('dev'));
app.use(express.json());

// Routes
app.use('/bookmarks', bookmarkRoutes);
app.use('/collections', collectionRoutes);
app.use('/tags', tagRoutes);
app.use('/search', searchRoutes);

// Error handler (MUST be last)
app.use(errorHandler);

app.listen(PORT, () => {
  console.log(`BookmarkAPI server running on port ${PORT}`);
});

export default app;
