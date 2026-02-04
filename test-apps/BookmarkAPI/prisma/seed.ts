import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  // Clear existing data in correct order
  await prisma.bookmarkTag.deleteMany({});
  await prisma.bookmark.deleteMany({});
  await prisma.tag.deleteMany({});
  await prisma.collection.deleteMany({});

  console.log('Cleared existing data');

  // Create collections
  const devCollection = await prisma.collection.create({
    data: {
      name: 'Development',
      description: 'Web development resources and documentation',
      color: '#3B82F6',
    },
  });

  const designCollection = await prisma.collection.create({
    data: {
      name: 'Design',
      description: 'UI/UX design inspiration and tools',
      color: '#8B5CF6',
    },
  });

  const newsCollection = await prisma.collection.create({
    data: {
      name: 'News',
      description: 'Tech news and industry updates',
      color: '#EF4444',
    },
  });

  console.log('Created 3 collections');

  // Create tags
  const jsTag = await prisma.tag.create({ data: { name: 'javascript' } });
  const cssTag = await prisma.tag.create({ data: { name: 'css' } });
  const reactTag = await prisma.tag.create({ data: { name: 'react' } });
  const tutorialTag = await prisma.tag.create({ data: { name: 'tutorial' } });
  const referenceTag = await prisma.tag.create({ data: { name: 'reference' } });

  console.log('Created 5 tags');

  // Create 10 bookmarks with tags
  await prisma.bookmark.create({
    data: {
      url: 'https://developer.mozilla.org/en-US/docs/Web/JavaScript',
      title: 'MDN JavaScript Documentation',
      description: 'Comprehensive JavaScript reference and guides',
      favicon: 'https://developer.mozilla.org/favicon.ico',
      collectionId: devCollection.id,
      tags: {
        create: [
          { tagId: jsTag.id },
          { tagId: referenceTag.id },
        ],
      },
    },
  });

  await prisma.bookmark.create({
    data: {
      url: 'https://react.dev',
      title: 'React Documentation',
      description: 'Official React documentation and getting started guide',
      favicon: 'https://react.dev/favicon.ico',
      collectionId: devCollection.id,
      tags: {
        create: [
          { tagId: reactTag.id },
          { tagId: jsTag.id },
          { tagId: referenceTag.id },
        ],
      },
    },
  });

  await prisma.bookmark.create({
    data: {
      url: 'https://css-tricks.com/snippets/css/a-guide-to-flexbox/',
      title: 'A Complete Guide to Flexbox',
      description: 'Comprehensive guide to CSS Flexbox layout',
      favicon: 'https://css-tricks.com/favicon.ico',
      collectionId: devCollection.id,
      tags: {
        create: [
          { tagId: cssTag.id },
          { tagId: referenceTag.id },
        ],
      },
    },
  });

  await prisma.bookmark.create({
    data: {
      url: 'https://javascript.info',
      title: 'The Modern JavaScript Tutorial',
      description: 'From the basics to advanced topics with simple explanations',
      favicon: 'https://javascript.info/img/favicon/favicon.png',
      collectionId: devCollection.id,
      tags: {
        create: [
          { tagId: jsTag.id },
          { tagId: tutorialTag.id },
        ],
      },
    },
  });

  await prisma.bookmark.create({
    data: {
      url: 'https://www.typescriptlang.org/docs/',
      title: 'TypeScript Documentation',
      description: 'Official TypeScript handbook and reference',
      favicon: 'https://www.typescriptlang.org/favicon.ico',
      collectionId: devCollection.id,
      tags: {
        create: [
          { tagId: jsTag.id },
          { tagId: referenceTag.id },
        ],
      },
    },
  });

  await prisma.bookmark.create({
    data: {
      url: 'https://dribbble.com',
      title: 'Dribbble - Design Inspiration',
      description: 'Discover the world\'s top designers and creative professionals',
      favicon: 'https://dribbble.com/favicon.ico',
      collectionId: designCollection.id,
      tags: {
        create: [
          { tagId: cssTag.id },
          { tagId: referenceTag.id },
        ],
      },
    },
  });

  await prisma.bookmark.create({
    data: {
      url: 'https://www.figma.com/community',
      title: 'Figma Community',
      description: 'Free design resources and UI kits',
      favicon: 'https://www.figma.com/favicon.ico',
      collectionId: designCollection.id,
      tags: {
        create: [
          { tagId: referenceTag.id },
          { tagId: tutorialTag.id },
        ],
      },
    },
  });

  await prisma.bookmark.create({
    data: {
      url: 'https://tailwindcss.com/docs',
      title: 'Tailwind CSS Documentation',
      description: 'Utility-first CSS framework documentation',
      favicon: 'https://tailwindcss.com/favicon.ico',
      collectionId: designCollection.id,
      tags: {
        create: [
          { tagId: cssTag.id },
          { tagId: tutorialTag.id },
          { tagId: referenceTag.id },
        ],
      },
    },
  });

  await prisma.bookmark.create({
    data: {
      url: 'https://news.ycombinator.com',
      title: 'Hacker News',
      description: 'Technology and startup news from Y Combinator',
      favicon: 'https://news.ycombinator.com/favicon.ico',
      collectionId: newsCollection.id,
      tags: {
        create: [
          { tagId: jsTag.id },
          { tagId: referenceTag.id },
        ],
      },
    },
  });

  await prisma.bookmark.create({
    data: {
      url: 'https://www.theverge.com/tech',
      title: 'The Verge - Tech',
      description: 'Latest technology news and reviews',
      favicon: 'https://www.theverge.com/favicon.ico',
      collectionId: newsCollection.id,
      tags: {
        create: [
          { tagId: referenceTag.id },
          { tagId: tutorialTag.id },
        ],
      },
    },
  });

  console.log('Created 10 bookmarks with tags');
  console.log('Seed completed successfully!');
}

main()
  .catch((e) => {
    console.error('Seed error:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
