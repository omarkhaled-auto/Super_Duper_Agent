import request from 'supertest';
import { app } from '../src/server';
import { bookmarkStore } from '../src/store';

/**
 * Helper function to create test bookmarks
 * @param data - Partial bookmark data to override defaults
 * @returns Promise with supertest response
 */
const createTestBookmark = async (data = {}) => {
  const defaultData = {
    title: 'Test Bookmark',
    url: 'https://example.com',
    tags: ['test']
  };
  return request(app)
    .post('/bookmarks')
    .send({ ...defaultData, ...data });
};

describe('Bookmarks API', () => {
  beforeEach(() => {
    bookmarkStore.clear();
  });

  // ===========================================================================
  // TASK-013: GET /bookmarks Tests
  // ===========================================================================
  describe('GET /bookmarks', () => {
    it('returns 200 with empty array when no bookmarks exist', async () => {
      const response = await request(app)
        .get('/bookmarks')
        .expect(200)
        .expect('Content-Type', /application\/json/);

      expect(response.body).toEqual([]);
    });

    it('returns 200 with bookmarks array when bookmarks exist', async () => {
      // Create a bookmark first
      await createTestBookmark({ title: 'First Bookmark', url: 'https://first.com' });
      await createTestBookmark({ title: 'Second Bookmark', url: 'https://second.com' });

      const response = await request(app)
        .get('/bookmarks')
        .expect(200)
        .expect('Content-Type', /application\/json/);

      expect(response.body).toBeInstanceOf(Array);
      expect(response.body).toHaveLength(2);
      expect(response.body[0]).toHaveProperty('title', 'First Bookmark');
      expect(response.body[1]).toHaveProperty('title', 'Second Bookmark');
    });

    it('response Content-Type is application/json', async () => {
      const response = await request(app)
        .get('/bookmarks')
        .expect(200);

      expect(response.headers['content-type']).toMatch(/application\/json/);
    });
  });

  // ===========================================================================
  // TASK-014: POST /bookmarks Tests
  // ===========================================================================
  describe('POST /bookmarks', () => {
    it('creates bookmark with valid data and returns 201', async () => {
      const bookmarkData = {
        title: 'New Bookmark',
        url: 'https://newsite.com',
        tags: ['new', 'test']
      };

      const response = await request(app)
        .post('/bookmarks')
        .send(bookmarkData)
        .expect(201)
        .expect('Content-Type', /application\/json/);

      expect(response.body).toHaveProperty('title', 'New Bookmark');
      expect(response.body).toHaveProperty('url', 'https://newsite.com');
      expect(response.body.tags).toEqual(['new', 'test']);
    });

    it('created bookmark has auto-generated id and created_at', async () => {
      const response = await createTestBookmark();

      expect(response.status).toBe(201);
      expect(response.body).toHaveProperty('id');
      expect(typeof response.body.id).toBe('string');
      expect(response.body.id).toMatch(/^[0-9a-f-]{36}$/); // UUID format
      expect(response.body).toHaveProperty('created_at');
      expect(new Date(response.body.created_at)).toBeInstanceOf(Date);
    });

    it('returns 400 when title is missing', async () => {
      const response = await request(app)
        .post('/bookmarks')
        .send({ url: 'https://example.com' })
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toHaveProperty('message');
      expect(response.body.error).toHaveProperty('statusCode', 400);
    });

    it('returns 400 when url is invalid', async () => {
      const response = await request(app)
        .post('/bookmarks')
        .send({ title: 'Test', url: 'not-a-valid-url' })
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toHaveProperty('message');
    });

    it('returns 400 with descriptive error message', async () => {
      const response = await request(app)
        .post('/bookmarks')
        .send({ title: '', url: 'https://example.com' })
        .expect(400);

      expect(response.body.error.message).toBeTruthy();
      expect(typeof response.body.error.message).toBe('string');
      expect(response.body.error.message.length).toBeGreaterThan(0);
    });
  });

  // ===========================================================================
  // TASK-015: GET /bookmarks/:id Tests
  // ===========================================================================
  describe('GET /bookmarks/:id', () => {
    it('returns 200 with bookmark when ID exists', async () => {
      const createResponse = await createTestBookmark({ title: 'Find Me' });
      const bookmarkId = createResponse.body.id;

      const response = await request(app)
        .get(`/bookmarks/${bookmarkId}`)
        .expect(200)
        .expect('Content-Type', /application\/json/);

      expect(response.body).toHaveProperty('id', bookmarkId);
      expect(response.body).toHaveProperty('title', 'Find Me');
    });

    it('returns 404 when ID does not exist', async () => {
      const nonExistentId = '00000000-0000-0000-0000-000000000000';

      const response = await request(app)
        .get(`/bookmarks/${nonExistentId}`)
        .expect(404);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toHaveProperty('statusCode', 404);
      expect(response.body.error).toHaveProperty('message');
    });

    it('returned bookmark matches created bookmark', async () => {
      const originalData = {
        title: 'Original Title',
        url: 'https://original.com',
        tags: ['original', 'match']
      };
      const createResponse = await createTestBookmark(originalData);
      const bookmarkId = createResponse.body.id;

      const response = await request(app)
        .get(`/bookmarks/${bookmarkId}`)
        .expect(200);

      expect(response.body.title).toBe(originalData.title);
      expect(response.body.url).toBe(originalData.url);
      expect(response.body.tags).toEqual(originalData.tags);
      expect(response.body.id).toBe(createResponse.body.id);
      expect(response.body.created_at).toBe(createResponse.body.created_at);
    });
  });

  // ===========================================================================
  // TASK-016: PUT /bookmarks/:id Tests
  // ===========================================================================
  describe('PUT /bookmarks/:id', () => {
    it('returns 200 with updated bookmark when valid', async () => {
      const createResponse = await createTestBookmark({ title: 'Before Update' });
      const bookmarkId = createResponse.body.id;

      const response = await request(app)
        .put(`/bookmarks/${bookmarkId}`)
        .send({ title: 'After Update' })
        .expect(200)
        .expect('Content-Type', /application\/json/);

      expect(response.body).toHaveProperty('title', 'After Update');
      expect(response.body).toHaveProperty('id', bookmarkId);
    });

    it('updated fields are changed, unchanged fields preserved', async () => {
      const createResponse = await createTestBookmark({
        title: 'Original Title',
        url: 'https://original.com',
        tags: ['original']
      });
      const bookmarkId = createResponse.body.id;
      const originalCreatedAt = createResponse.body.created_at;

      const response = await request(app)
        .put(`/bookmarks/${bookmarkId}`)
        .send({ title: 'Updated Title' })
        .expect(200);

      // Updated field should be changed
      expect(response.body.title).toBe('Updated Title');

      // Unchanged fields should be preserved
      expect(response.body.url).toBe('https://original.com');
      expect(response.body.tags).toEqual(['original']);
      expect(response.body.id).toBe(bookmarkId);
      expect(response.body.created_at).toBe(originalCreatedAt);
    });

    it('returns 404 when ID does not exist', async () => {
      const nonExistentId = '00000000-0000-0000-0000-000000000000';

      const response = await request(app)
        .put(`/bookmarks/${nonExistentId}`)
        .send({ title: 'Update Non-Existent' })
        .expect(404);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toHaveProperty('statusCode', 404);
    });

    it('returns 400 when update data is invalid (empty title)', async () => {
      const createResponse = await createTestBookmark();
      const bookmarkId = createResponse.body.id;

      const response = await request(app)
        .put(`/bookmarks/${bookmarkId}`)
        .send({ title: '' })
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toHaveProperty('statusCode', 400);
    });
  });

  // ===========================================================================
  // TASK-017: DELETE /bookmarks/:id Tests
  // ===========================================================================
  describe('DELETE /bookmarks/:id', () => {
    it('returns 204 when bookmark deleted successfully', async () => {
      const createResponse = await createTestBookmark();
      const bookmarkId = createResponse.body.id;

      await request(app)
        .delete(`/bookmarks/${bookmarkId}`)
        .expect(204);
    });

    it('bookmark no longer exists after deletion', async () => {
      const createResponse = await createTestBookmark();
      const bookmarkId = createResponse.body.id;

      // Delete the bookmark
      await request(app)
        .delete(`/bookmarks/${bookmarkId}`)
        .expect(204);

      // Verify it no longer exists
      await request(app)
        .get(`/bookmarks/${bookmarkId}`)
        .expect(404);
    });

    it('returns 404 when ID does not exist', async () => {
      const nonExistentId = '00000000-0000-0000-0000-000000000000';

      const response = await request(app)
        .delete(`/bookmarks/${nonExistentId}`)
        .expect(404);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toHaveProperty('statusCode', 404);
    });
  });

  // ===========================================================================
  // TASK-018: Tag Filtering Tests
  // ===========================================================================
  describe('Tag Filtering', () => {
    it('returns only bookmarks with matching tag', async () => {
      await createTestBookmark({ title: 'JavaScript Guide', tags: ['javascript', 'programming'] });
      await createTestBookmark({ title: 'Python Guide', tags: ['python', 'programming'] });
      await createTestBookmark({ title: 'Cooking Recipe', tags: ['cooking'] });

      const response = await request(app)
        .get('/bookmarks?tag=javascript')
        .expect(200);

      expect(response.body).toHaveLength(1);
      expect(response.body[0]).toHaveProperty('title', 'JavaScript Guide');
    });

    it('tag filtering is case-insensitive', async () => {
      await createTestBookmark({ title: 'JS Tutorial', tags: ['JavaScript'] });
      await createTestBookmark({ title: 'Python Tutorial', tags: ['python'] });

      const response = await request(app)
        .get('/bookmarks?tag=javascript')
        .expect(200);

      expect(response.body).toHaveLength(1);
      expect(response.body[0]).toHaveProperty('title', 'JS Tutorial');
    });

    it('returns empty array when no bookmarks match tag', async () => {
      await createTestBookmark({ title: 'Test Bookmark', tags: ['test'] });

      const response = await request(app)
        .get('/bookmarks?tag=nonexistent')
        .expect(200);

      expect(response.body).toEqual([]);
    });
  });

  // ===========================================================================
  // TASK-019: Search Filtering Tests
  // ===========================================================================
  describe('Search Filtering', () => {
    it('returns bookmarks with title containing search term', async () => {
      await createTestBookmark({ title: 'React Tutorial' });
      await createTestBookmark({ title: 'Vue Tutorial' });
      await createTestBookmark({ title: 'Angular Guide' });

      const response = await request(app)
        .get('/bookmarks?search=Tutorial')
        .expect(200);

      expect(response.body).toHaveLength(2);
      expect(response.body.map((b: { title: string }) => b.title)).toContain('React Tutorial');
      expect(response.body.map((b: { title: string }) => b.title)).toContain('Vue Tutorial');
    });

    it('search is case-insensitive', async () => {
      await createTestBookmark({ title: 'UPPERCASE TITLE' });
      await createTestBookmark({ title: 'lowercase title' });
      await createTestBookmark({ title: 'Other Bookmark' });

      const response = await request(app)
        .get('/bookmarks?search=title')
        .expect(200);

      expect(response.body).toHaveLength(2);
    });

    it('returns empty array when no titles match', async () => {
      await createTestBookmark({ title: 'Hello World' });

      const response = await request(app)
        .get('/bookmarks?search=xyz123nonexistent')
        .expect(200);

      expect(response.body).toEqual([]);
    });
  });

  // ===========================================================================
  // TASK-020: Combined Filters Tests
  // ===========================================================================
  describe('Combined Filters', () => {
    it('combined tag and search filters work (AND logic)', async () => {
      await createTestBookmark({ title: 'React Tutorial', tags: ['react', 'frontend'] });
      await createTestBookmark({ title: 'React Guide', tags: ['react', 'frontend'] });
      await createTestBookmark({ title: 'Vue Tutorial', tags: ['vue', 'frontend'] });
      await createTestBookmark({ title: 'Node Tutorial', tags: ['node', 'backend'] });

      const response = await request(app)
        .get('/bookmarks?tag=react&search=Tutorial')
        .expect(200);

      expect(response.body).toHaveLength(1);
      expect(response.body[0]).toHaveProperty('title', 'React Tutorial');
    });

    it('returns bookmarks matching both criteria', async () => {
      await createTestBookmark({ title: 'Advanced JavaScript', tags: ['javascript'] });
      await createTestBookmark({ title: 'JavaScript Basics', tags: ['javascript'] });
      await createTestBookmark({ title: 'Advanced Python', tags: ['python'] });

      const response = await request(app)
        .get('/bookmarks?tag=javascript&search=Advanced')
        .expect(200);

      expect(response.body).toHaveLength(1);
      expect(response.body[0]).toHaveProperty('title', 'Advanced JavaScript');
      expect(response.body[0].tags).toContain('javascript');
    });
  });

  // ===========================================================================
  // TASK-021: Validation Error Tests
  // ===========================================================================
  describe('Validation Errors', () => {
    it('empty title returns 400', async () => {
      const response = await request(app)
        .post('/bookmarks')
        .send({ title: '', url: 'https://example.com' })
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toHaveProperty('statusCode', 400);
      expect(response.body.error).toHaveProperty('message');
    });

    it('invalid URL protocol returns 400', async () => {
      const response = await request(app)
        .post('/bookmarks')
        .send({ title: 'Test', url: 'ftp://example.com' })
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toHaveProperty('statusCode', 400);
      expect(response.body.error.message).toMatch(/http|https|protocol/i);
    });

    it('error response format has message and statusCode', async () => {
      const response = await request(app)
        .post('/bookmarks')
        .send({ title: 'Test', url: 'invalid-url' })
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toHaveProperty('message');
      expect(typeof response.body.error.message).toBe('string');
      expect(response.body.error).toHaveProperty('statusCode');
      expect(typeof response.body.error.statusCode).toBe('number');
    });

    it('whitespace-only title returns 400', async () => {
      const response = await request(app)
        .post('/bookmarks')
        .send({ title: '   ', url: 'https://example.com' })
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toHaveProperty('statusCode', 400);
    });

    it('missing URL returns 400', async () => {
      const response = await request(app)
        .post('/bookmarks')
        .send({ title: 'Test Bookmark' })
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toHaveProperty('statusCode', 400);
    });

    it('invalid tags type returns 400', async () => {
      const response = await request(app)
        .post('/bookmarks')
        .send({ title: 'Test', url: 'https://example.com', tags: 'not-an-array' })
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toHaveProperty('statusCode', 400);
    });

    it('PUT with no fields returns 400', async () => {
      const createResponse = await createTestBookmark();
      const bookmarkId = createResponse.body.id;

      const response = await request(app)
        .put(`/bookmarks/${bookmarkId}`)
        .send({})
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toHaveProperty('statusCode', 400);
    });
  });
});
