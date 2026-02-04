// =============================================================================
// FlowBoard - Database Seed Script
// Run: npx prisma db seed
// =============================================================================

import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcrypt';

const prisma = new PrismaClient();

// =============================================================================
// HELPERS
// =============================================================================

async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10);
}

function daysFromNow(days: number): Date {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d;
}

// =============================================================================
// SEED DATA DEFINITIONS
// =============================================================================

const DEMO_PASSWORD = 'password123';

const USERS = [
  {
    id: 'user_alex',
    email: 'alex@flowboard.dev',
    name: 'Alex Rivera',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Alex',
  },
  {
    id: 'user_sam',
    email: 'sam@flowboard.dev',
    name: 'Sam Chen',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Sam',
  },
  {
    id: 'user_jordan',
    email: 'jordan@flowboard.dev',
    name: 'Jordan Blake',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Jordan',
  },
] as const;

const PROJECTS = [
  {
    id: 'proj_flowboard',
    name: 'FlowBoard v2',
    description: 'Next generation of our project management platform with real-time collaboration, Kanban boards, and advanced analytics.',
    icon: 'rocket',
    color: '#8B5CF6',
  },
  {
    id: 'proj_marketing',
    name: 'Marketing Site',
    description: 'Company marketing website redesign with new branding, SEO optimization, and conversion-focused landing pages.',
    icon: 'globe',
    color: '#3B82F6',
  },
  {
    id: 'proj_mobile',
    name: 'Mobile App',
    description: 'Cross-platform mobile application using React Native with offline support, push notifications, and biometric authentication.',
    icon: 'smartphone',
    color: '#22C55E',
  },
] as const;

// All 3 users are members of all 3 projects (Alex=ADMIN, Sam=MEMBER, Jordan=MEMBER)
const PROJECT_MEMBERS = [
  // FlowBoard v2
  { userId: 'user_alex',   projectId: 'proj_flowboard', role: 'ADMIN' },
  { userId: 'user_sam',    projectId: 'proj_flowboard', role: 'MEMBER' },
  { userId: 'user_jordan', projectId: 'proj_flowboard', role: 'MEMBER' },
  // Marketing Site
  { userId: 'user_alex',   projectId: 'proj_marketing', role: 'ADMIN' },
  { userId: 'user_sam',    projectId: 'proj_marketing', role: 'MEMBER' },
  { userId: 'user_jordan', projectId: 'proj_marketing', role: 'MEMBER' },
  // Mobile App
  { userId: 'user_alex',   projectId: 'proj_mobile',    role: 'ADMIN' },
  { userId: 'user_sam',    projectId: 'proj_mobile',    role: 'MEMBER' },
  { userId: 'user_jordan', projectId: 'proj_mobile',    role: 'MEMBER' },
];

// 5 labels per project: Bug (red), Feature (blue), Improvement (green), Documentation (yellow), Design (purple)
const LABELS = [
  // FlowBoard v2
  { id: 'lbl_bug_fb',     name: 'Bug',           color: '#EF4444', projectId: 'proj_flowboard' },
  { id: 'lbl_feat_fb',    name: 'Feature',        color: '#3B82F6', projectId: 'proj_flowboard' },
  { id: 'lbl_imp_fb',     name: 'Improvement',    color: '#22C55E', projectId: 'proj_flowboard' },
  { id: 'lbl_docs_fb',    name: 'Documentation',  color: '#EAB308', projectId: 'proj_flowboard' },
  { id: 'lbl_design_fb',  name: 'Design',         color: '#8B5CF6', projectId: 'proj_flowboard' },
  // Marketing Site
  { id: 'lbl_bug_mkt',    name: 'Bug',           color: '#EF4444', projectId: 'proj_marketing' },
  { id: 'lbl_feat_mkt',   name: 'Feature',        color: '#3B82F6', projectId: 'proj_marketing' },
  { id: 'lbl_imp_mkt',    name: 'Improvement',    color: '#22C55E', projectId: 'proj_marketing' },
  { id: 'lbl_docs_mkt',   name: 'Documentation',  color: '#EAB308', projectId: 'proj_marketing' },
  { id: 'lbl_design_mkt', name: 'Design',         color: '#8B5CF6', projectId: 'proj_marketing' },
  // Mobile App
  { id: 'lbl_bug_mob',    name: 'Bug',           color: '#EF4444', projectId: 'proj_mobile' },
  { id: 'lbl_feat_mob',   name: 'Feature',        color: '#3B82F6', projectId: 'proj_mobile' },
  { id: 'lbl_imp_mob',    name: 'Improvement',    color: '#22C55E', projectId: 'proj_mobile' },
  { id: 'lbl_docs_mob',   name: 'Documentation',  color: '#EAB308', projectId: 'proj_mobile' },
  { id: 'lbl_design_mob', name: 'Design',         color: '#8B5CF6', projectId: 'proj_mobile' },
];

// ---------------------------------------------------------------------------
// TASKS — 33 total across 3 projects
// ---------------------------------------------------------------------------

interface TaskSeed {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  position: number;
  projectId: string;
  creatorId: string;
  assigneeId: string | null;
  dueDate: Date | null;
  labelIds: string[];
}

const TASKS: TaskSeed[] = [
  // =========================================================================
  // PROJECT 1 — FlowBoard v2 (15 tasks, 3 per status)
  // =========================================================================

  // BACKLOG (3)
  {
    id: 'task_fb_01', title: 'Implement WebSocket real-time sync',
    description: 'Add Socket.io integration for real-time board updates. When one user moves a card, all other viewers should see the change instantly without page refresh.',
    status: 'BACKLOG', priority: 'HIGH', position: 0,
    projectId: 'proj_flowboard', creatorId: 'user_alex', assigneeId: null,
    dueDate: null, labelIds: ['lbl_feat_fb'],
  },
  {
    id: 'task_fb_02', title: 'Add keyboard shortcuts for power users',
    description: 'Implement keyboard navigation: arrow keys to move between cards, Enter to open, Escape to close, N for new task, / to search. Include a shortcut help modal (? key).',
    status: 'BACKLOG', priority: 'LOW', position: 1,
    projectId: 'proj_flowboard', creatorId: 'user_sam', assigneeId: null,
    dueDate: null, labelIds: ['lbl_feat_fb', 'lbl_imp_fb'],
  },
  {
    id: 'task_fb_03', title: 'Design analytics dashboard mockups',
    description: 'Create Figma mockups for the project analytics page. Include: velocity chart, burndown chart, task distribution by status/priority, team workload visualization.',
    status: 'BACKLOG', priority: 'MEDIUM', position: 2,
    projectId: 'proj_flowboard', creatorId: 'user_alex', assigneeId: null,
    dueDate: null, labelIds: ['lbl_design_fb'],
  },

  // TODO (3)
  {
    id: 'task_fb_04', title: 'Build task filtering and search system',
    description: 'Implement a powerful filter bar that supports filtering by: status, priority, assignee, labels, due date range. Include a full-text search across task titles and descriptions.',
    status: 'TODO', priority: 'HIGH', position: 0,
    projectId: 'proj_flowboard', creatorId: 'user_alex', assigneeId: 'user_sam',
    dueDate: daysFromNow(7), labelIds: ['lbl_feat_fb'],
  },
  {
    id: 'task_fb_05', title: 'Create notification system for task updates',
    description: 'Build an in-app notification center. Users get notified when: assigned to a task, mentioned in a comment, task status changes, approaching due date. Include read/unread state and bulk actions.',
    status: 'TODO', priority: 'MEDIUM', position: 1,
    projectId: 'proj_flowboard', creatorId: 'user_sam', assigneeId: 'user_jordan',
    dueDate: daysFromNow(10), labelIds: ['lbl_feat_fb'],
  },
  {
    id: 'task_fb_06', title: 'Write API documentation with examples',
    description: 'Document all REST API endpoints with request/response examples, authentication flow, error codes, and rate limiting details. Use OpenAPI 3.1 spec format.',
    status: 'TODO', priority: 'LOW', position: 2,
    projectId: 'proj_flowboard', creatorId: 'user_alex', assigneeId: 'user_alex',
    dueDate: daysFromNow(14), labelIds: ['lbl_docs_fb'],
  },

  // IN_PROGRESS (3)
  {
    id: 'task_fb_07', title: 'Implement drag-and-drop for Kanban board',
    description: 'Use @dnd-kit/core for smooth drag-and-drop. Support: moving cards between columns, reordering within a column, multi-select drag. Persist position changes to the database.',
    status: 'IN_PROGRESS', priority: 'URGENT', position: 0,
    projectId: 'proj_flowboard', creatorId: 'user_alex', assigneeId: 'user_alex',
    dueDate: daysFromNow(2), labelIds: ['lbl_feat_fb'],
  },
  {
    id: 'task_fb_08', title: 'Fix task creation form validation errors',
    description: 'The task creation modal does not properly validate: empty titles (should show inline error), due dates in the past (should warn), description max length (10,000 chars). Also fix the form not resetting after submission.',
    status: 'IN_PROGRESS', priority: 'HIGH', position: 1,
    projectId: 'proj_flowboard', creatorId: 'user_jordan', assigneeId: 'user_sam',
    dueDate: daysFromNow(1), labelIds: ['lbl_bug_fb'],
  },
  {
    id: 'task_fb_09', title: 'Set up authentication with JWT refresh tokens',
    description: 'Implement secure auth flow: login returns access token (15min) + refresh token (7d). Auto-refresh on 401. Secure cookie storage for refresh token. Logout invalidates all tokens.',
    status: 'IN_PROGRESS', priority: 'URGENT', position: 2,
    projectId: 'proj_flowboard', creatorId: 'user_alex', assigneeId: 'user_jordan',
    dueDate: daysFromNow(3), labelIds: ['lbl_feat_fb'],
  },

  // IN_REVIEW (3)
  {
    id: 'task_fb_10', title: 'Design and implement project settings page',
    description: 'Project settings page with tabs: General (name, description, icon, color), Members (invite, remove, change roles), Labels (CRUD), Danger Zone (archive, delete). Responsive layout.',
    status: 'IN_REVIEW', priority: 'MEDIUM', position: 0,
    projectId: 'proj_flowboard', creatorId: 'user_alex', assigneeId: 'user_sam',
    dueDate: daysFromNow(0), labelIds: ['lbl_feat_fb', 'lbl_design_fb'],
  },
  {
    id: 'task_fb_11', title: 'Add dark mode theme support',
    description: 'Implement system-preference detection with manual toggle. Use CSS custom properties for theming. Persist choice in localStorage. Smooth 200ms transition between themes. Cover all components.',
    status: 'IN_REVIEW', priority: 'MEDIUM', position: 1,
    projectId: 'proj_flowboard', creatorId: 'user_sam', assigneeId: 'user_jordan',
    dueDate: daysFromNow(-1), labelIds: ['lbl_feat_fb', 'lbl_design_fb'],
  },
  {
    id: 'task_fb_12', title: 'Optimize database queries for board loading',
    description: 'Board loading takes 1.2s for projects with 50+ tasks due to N+1 queries. Use Prisma includes and selects to batch. Target: under 100ms for 100 tasks with all relations loaded.',
    status: 'IN_REVIEW', priority: 'HIGH', position: 2,
    projectId: 'proj_flowboard', creatorId: 'user_jordan', assigneeId: 'user_alex',
    dueDate: daysFromNow(-2), labelIds: ['lbl_imp_fb', 'lbl_bug_fb'],
  },

  // DONE (3)
  {
    id: 'task_fb_13', title: 'Set up project scaffolding with Turborepo',
    description: 'Initialize monorepo with Turborepo. Configure workspaces: client (React + Vite), server (Express + Prisma), shared (types + utilities). Set up TypeScript path aliases and shared configs.',
    status: 'DONE', priority: 'URGENT', position: 0,
    projectId: 'proj_flowboard', creatorId: 'user_alex', assigneeId: 'user_alex',
    dueDate: daysFromNow(-14), labelIds: ['lbl_feat_fb'],
  },
  {
    id: 'task_fb_14', title: 'Design component library with Tailwind CSS',
    description: 'Create reusable UI components: Button, Input, Select, Modal, Badge, Avatar, Card, Dropdown, Toast notifications. Follow consistent spacing, color, and typography system.',
    status: 'DONE', priority: 'HIGH', position: 1,
    projectId: 'proj_flowboard', creatorId: 'user_alex', assigneeId: 'user_sam',
    dueDate: daysFromNow(-10), labelIds: ['lbl_design_fb', 'lbl_feat_fb'],
  },
  {
    id: 'task_fb_15', title: 'Configure CI/CD pipeline with GitHub Actions',
    description: 'Set up GitHub Actions workflow: lint, typecheck, test on every PR. Auto-deploy main to staging. Include Prisma migration check and build validation.',
    status: 'DONE', priority: 'MEDIUM', position: 2,
    projectId: 'proj_flowboard', creatorId: 'user_sam', assigneeId: 'user_sam',
    dueDate: daysFromNow(-12), labelIds: ['lbl_imp_fb'],
  },

  // =========================================================================
  // PROJECT 2 — Marketing Site (10 tasks, 2 per status)
  // =========================================================================

  // BACKLOG (2)
  {
    id: 'task_mkt_01', title: 'Create blog section with MDX support',
    description: 'Set up a blog using MDX for content authoring. Features: syntax highlighting, table of contents, reading time estimate, author bios, social sharing buttons.',
    status: 'BACKLOG', priority: 'LOW', position: 0,
    projectId: 'proj_marketing', creatorId: 'user_alex', assigneeId: null,
    dueDate: null, labelIds: ['lbl_feat_mkt'],
  },
  {
    id: 'task_mkt_02', title: 'Design customer testimonials section',
    description: 'Auto-rotating carousel for customer testimonials. Include customer photo, name, company, role, and quote. Manual navigation with dots and arrows. Pause on hover.',
    status: 'BACKLOG', priority: 'LOW', position: 1,
    projectId: 'proj_marketing', creatorId: 'user_sam', assigneeId: null,
    dueDate: null, labelIds: ['lbl_design_mkt'],
  },

  // TODO (2)
  {
    id: 'task_mkt_03', title: 'Implement contact form with email delivery',
    description: 'Contact page form that sends submissions via SendGrid API. Fields: name, email, company, message. Include CAPTCHA, rate limiting, and confirmation email to the submitter.',
    status: 'TODO', priority: 'MEDIUM', position: 0,
    projectId: 'proj_marketing', creatorId: 'user_alex', assigneeId: 'user_jordan',
    dueDate: daysFromNow(8), labelIds: ['lbl_feat_mkt'],
  },
  {
    id: 'task_mkt_04', title: 'Write SEO meta tags and structured data',
    description: 'Add proper title, meta description, Open Graph, Twitter Card tags to every page. Implement JSON-LD structured data for organization, products, and FAQ sections.',
    status: 'TODO', priority: 'MEDIUM', position: 1,
    projectId: 'proj_marketing', creatorId: 'user_sam', assigneeId: 'user_sam',
    dueDate: daysFromNow(6), labelIds: ['lbl_imp_mkt', 'lbl_docs_mkt'],
  },

  // IN_PROGRESS (2)
  {
    id: 'task_mkt_05', title: 'Build pricing page with tier comparison',
    description: 'Three-tier pricing table: Free, Pro ($12/mo), Enterprise (custom). Monthly/annual toggle with discount badge. Feature comparison matrix. FAQ section below.',
    status: 'IN_PROGRESS', priority: 'HIGH', position: 0,
    projectId: 'proj_marketing', creatorId: 'user_alex', assigneeId: 'user_alex',
    dueDate: daysFromNow(3), labelIds: ['lbl_feat_mkt', 'lbl_design_mkt'],
  },
  {
    id: 'task_mkt_06', title: 'Fix hero section animation jank on mobile',
    description: 'The hero gradient animation causes frame drops on iOS Safari and low-end Android devices. Investigate GPU compositing issues. Consider reducing animation complexity for mobile viewports.',
    status: 'IN_PROGRESS', priority: 'URGENT', position: 1,
    projectId: 'proj_marketing', creatorId: 'user_jordan', assigneeId: 'user_sam',
    dueDate: daysFromNow(1), labelIds: ['lbl_bug_mkt'],
  },

  // IN_REVIEW (2)
  {
    id: 'task_mkt_07', title: 'Design and implement responsive navigation',
    description: 'Desktop: horizontal links with dropdown menus. Mobile: hamburger menu with full-screen overlay. Sticky header on scroll with subtle shadow. Active page indicator.',
    status: 'IN_REVIEW', priority: 'HIGH', position: 0,
    projectId: 'proj_marketing', creatorId: 'user_alex', assigneeId: 'user_jordan',
    dueDate: daysFromNow(-1), labelIds: ['lbl_feat_mkt', 'lbl_design_mkt'],
  },
  {
    id: 'task_mkt_08', title: 'Integrate Plausible analytics tracking',
    description: 'Add Plausible Analytics script with custom events for: CTA clicks, pricing toggle interactions, signup funnel steps, scroll depth tracking. GDPR compliant, no cookie banner needed.',
    status: 'IN_REVIEW', priority: 'LOW', position: 1,
    projectId: 'proj_marketing', creatorId: 'user_sam', assigneeId: 'user_sam',
    dueDate: daysFromNow(0), labelIds: ['lbl_imp_mkt'],
  },

  // DONE (2)
  {
    id: 'task_mkt_09', title: 'Design new homepage hero section',
    description: 'Visually striking hero with animated gradient background, headline in brand typeface, primary and secondary CTA buttons with hover micro-interactions. Responsive down to 320px.',
    status: 'DONE', priority: 'HIGH', position: 0,
    projectId: 'proj_marketing', creatorId: 'user_alex', assigneeId: 'user_alex',
    dueDate: daysFromNow(-7), labelIds: ['lbl_design_mkt', 'lbl_feat_mkt'],
  },
  {
    id: 'task_mkt_10', title: 'Set up Next.js project with Tailwind CSS',
    description: 'Initialize Next.js 14 project with App Router, Tailwind CSS, TypeScript. Configure custom fonts, color palette, spacing scale. Set up ESLint, Prettier, and Husky pre-commit hooks.',
    status: 'DONE', priority: 'URGENT', position: 1,
    projectId: 'proj_marketing', creatorId: 'user_alex', assigneeId: 'user_sam',
    dueDate: daysFromNow(-14), labelIds: ['lbl_feat_mkt'],
  },

  // =========================================================================
  // PROJECT 3 — Mobile App (8 tasks, varied distribution)
  // =========================================================================

  // BACKLOG (2)
  {
    id: 'task_mob_01', title: 'Implement offline-first data sync',
    description: 'Configure WatermelonDB for local-first storage. Implement sync protocol with backend API. Handle conflict resolution with last-write-wins strategy. Sync indicator in the UI.',
    status: 'BACKLOG', priority: 'HIGH', position: 0,
    projectId: 'proj_mobile', creatorId: 'user_alex', assigneeId: null,
    dueDate: null, labelIds: ['lbl_feat_mob'],
  },
  {
    id: 'task_mob_02', title: 'Add localization for Spanish and French',
    description: 'Use react-native-localize + i18next. Extract all user-facing strings. Translate to Spanish (es) and French (fr). Handle RTL preparation. Date and number formatting per locale.',
    status: 'BACKLOG', priority: 'LOW', position: 1,
    projectId: 'proj_mobile', creatorId: 'user_sam', assigneeId: null,
    dueDate: null, labelIds: ['lbl_feat_mob', 'lbl_docs_mob'],
  },

  // TODO (1)
  {
    id: 'task_mob_03', title: 'Build push notification service',
    description: 'Set up Firebase Cloud Messaging for Android and APNs for iOS. Rich notifications with images, deep linking to specific screens, notification preferences per channel.',
    status: 'TODO', priority: 'HIGH', position: 0,
    projectId: 'proj_mobile', creatorId: 'user_alex', assigneeId: 'user_jordan',
    dueDate: daysFromNow(5), labelIds: ['lbl_feat_mob'],
  },

  // IN_PROGRESS (2)
  {
    id: 'task_mob_04', title: 'Implement biometric authentication flow',
    description: 'Support Face ID (iOS) and Fingerprint (Android). Fallback to PIN code. Integrate with react-native-biometrics. Store tokens securely in Keychain/Keystore. Include opt-in prompt.',
    status: 'IN_PROGRESS', priority: 'URGENT', position: 0,
    projectId: 'proj_mobile', creatorId: 'user_alex', assigneeId: 'user_alex',
    dueDate: daysFromNow(2), labelIds: ['lbl_feat_mob'],
  },
  {
    id: 'task_mob_05', title: 'Fix crash on Android 12 camera permission',
    description: 'App crashes with SecurityException when launching camera on Android 12+. Missing CAMERA permission in manifest or runtime permission handling issue. Affects profile photo upload.',
    status: 'IN_PROGRESS', priority: 'URGENT', position: 1,
    projectId: 'proj_mobile', creatorId: 'user_jordan', assigneeId: 'user_sam',
    dueDate: daysFromNow(0), labelIds: ['lbl_bug_mob'],
  },

  // IN_REVIEW (1)
  {
    id: 'task_mob_06', title: 'Create onboarding flow with Lottie animations',
    description: 'Three-screen onboarding: welcome and value proposition, key features walkthrough, permission requests (notifications, location). Skippable with a Get Started CTA. Swipeable page view.',
    status: 'IN_REVIEW', priority: 'MEDIUM', position: 0,
    projectId: 'proj_mobile', creatorId: 'user_sam', assigneeId: 'user_jordan',
    dueDate: daysFromNow(1), labelIds: ['lbl_feat_mob', 'lbl_design_mob'],
  },

  // DONE (2)
  {
    id: 'task_mob_07', title: 'Set up React Native project with Expo',
    description: 'Initialize Expo managed workflow project. Configure TypeScript, ESLint, Prettier. Set up navigation with React Navigation. Install core dependencies. Configure EAS Build for both platforms.',
    status: 'DONE', priority: 'URGENT', position: 0,
    projectId: 'proj_mobile', creatorId: 'user_alex', assigneeId: 'user_alex',
    dueDate: daysFromNow(-21), labelIds: ['lbl_feat_mob'],
  },
  {
    id: 'task_mob_08', title: 'Build app shell with bottom tab navigation',
    description: 'Create the main app layout with bottom tabs: Home, Projects, Notifications, Profile. Implement stack navigators within each tab. Add transition animations between screens.',
    status: 'DONE', priority: 'HIGH', position: 1,
    projectId: 'proj_mobile', creatorId: 'user_alex', assigneeId: 'user_sam',
    dueDate: daysFromNow(-16), labelIds: ['lbl_feat_mob', 'lbl_design_mob'],
  },
];

// ---------------------------------------------------------------------------
// SUBTASKS (for selected tasks)
// ---------------------------------------------------------------------------

interface SubtaskSeed {
  title: string;
  completed: boolean;
  position: number;
  taskId: string;
}

const SUBTASKS: SubtaskSeed[] = [
  // task_fb_07 - Drag and drop (3 subtasks)
  { title: 'Set up @dnd-kit/core and sortable context',      completed: true,  position: 0, taskId: 'task_fb_07' },
  { title: 'Implement column-to-column card movement',        completed: true,  position: 1, taskId: 'task_fb_07' },
  { title: 'Persist position changes via API call',           completed: false, position: 2, taskId: 'task_fb_07' },

  // task_fb_09 - Auth with JWT (3 subtasks)
  { title: 'Implement login endpoint with access + refresh tokens', completed: true,  position: 0, taskId: 'task_fb_09' },
  { title: 'Build token refresh middleware',                        completed: false, position: 1, taskId: 'task_fb_09' },
  { title: 'Add secure cookie storage for refresh token',           completed: false, position: 2, taskId: 'task_fb_09' },

  // task_fb_10 - Project settings (3 subtasks)
  { title: 'Build General settings tab (name, description, icon)',  completed: true,  position: 0, taskId: 'task_fb_10' },
  { title: 'Build Members tab with invite and role management',     completed: true,  position: 1, taskId: 'task_fb_10' },
  { title: 'Build Danger Zone tab (archive, delete project)',       completed: true,  position: 2, taskId: 'task_fb_10' },

  // task_mkt_05 - Pricing page (2 subtasks)
  { title: 'Design tier cards with monthly/annual toggle',  completed: true,  position: 0, taskId: 'task_mkt_05' },
  { title: 'Build feature comparison matrix below pricing', completed: false, position: 1, taskId: 'task_mkt_05' },

  // task_mob_04 - Biometric auth (3 subtasks)
  { title: 'Integrate react-native-biometrics library',      completed: true,  position: 0, taskId: 'task_mob_04' },
  { title: 'Implement PIN code fallback flow',                completed: false, position: 1, taskId: 'task_mob_04' },
  { title: 'Secure token storage in Keychain / Keystore',    completed: false, position: 2, taskId: 'task_mob_04' },

  // task_mob_06 - Onboarding flow (2 subtasks)
  { title: 'Create Lottie animations for each screen',       completed: true,  position: 0, taskId: 'task_mob_06' },
  { title: 'Build swipeable page view with skip button',     completed: true,  position: 1, taskId: 'task_mob_06' },
];

// ---------------------------------------------------------------------------
// COMMENTS
// ---------------------------------------------------------------------------

interface CommentSeed {
  content: string;
  taskId: string;
  authorId: string;
  daysAgo: number;
}

const COMMENTS: CommentSeed[] = [
  // FlowBoard v2 comments
  {
    content: 'The drag-and-drop is feeling really smooth! One thing -- can we add a subtle scale animation when picking up a card?',
    taskId: 'task_fb_07', authorId: 'user_sam', daysAgo: 2,
  },
  {
    content: 'Good call. I added a 1.02 scale transform on drag start. Looks much more polished now.',
    taskId: 'task_fb_07', authorId: 'user_alex', daysAgo: 1,
  },
  {
    content: 'The form validation issue is more widespread than I initially thought. The date picker also allows selecting weekends when it should not for business-only projects.',
    taskId: 'task_fb_08', authorId: 'user_jordan', daysAgo: 3,
  },
  {
    content: 'I have been testing the dark mode extensively. Looks great everywhere except the dropdown menus -- the border color is too harsh. Maybe use a softer gray?',
    taskId: 'task_fb_11', authorId: 'user_alex', daysAgo: 1,
  },
  {
    content: 'Fixed! Changed from gray-700 to gray-600/50 with backdrop blur. Much softer now.',
    taskId: 'task_fb_11', authorId: 'user_jordan', daysAgo: 0,
  },
  {
    content: 'The N+1 fix reduced board load time from 1.2s to 80ms. Huge improvement. Ready for review.',
    taskId: 'task_fb_12', authorId: 'user_alex', daysAgo: 0,
  },
  {
    content: 'For the auth flow, should we support OAuth providers (Google, GitHub) in addition to email/password? Or save that for a later sprint?',
    taskId: 'task_fb_09', authorId: 'user_sam', daysAgo: 4,
  },
  {
    content: 'Let us nail email/password first. OAuth can be a fast follow -- the token infrastructure will be the same.',
    taskId: 'task_fb_09', authorId: 'user_alex', daysAgo: 4,
  },

  // Marketing Site comments
  {
    content: 'The pricing page is looking sharp. Can we add a popular badge on the Pro tier to guide users toward it?',
    taskId: 'task_mkt_05', authorId: 'user_jordan', daysAgo: 1,
  },
  {
    content: 'Absolutely. Adding a purple gradient badge with "Most Popular" text. It will really draw the eye.',
    taskId: 'task_mkt_05', authorId: 'user_alex', daysAgo: 0,
  },
  {
    content: 'Safari users are reporting the hero animation is causing significant battery drain. We might need to use prefers-reduced-motion media query as well.',
    taskId: 'task_mkt_06', authorId: 'user_sam', daysAgo: 1,
  },

  // Mobile App comments
  {
    content: 'The crash is consistent on Pixel 7 running Android 12. Logcat shows SecurityException at CameraActivity.java:142. Definitely a missing runtime permission check.',
    taskId: 'task_mob_05', authorId: 'user_jordan', daysAgo: 2,
  },
  {
    content: 'Found it. We are requesting the permission but not waiting for the result before launching the intent. Fix is straightforward.',
    taskId: 'task_mob_05', authorId: 'user_sam', daysAgo: 1,
  },
  {
    content: 'The onboarding animations look fantastic! The transition between screens is silky smooth. Great work on the Lottie files.',
    taskId: 'task_mob_06', authorId: 'user_alex', daysAgo: 0,
  },
  {
    content: 'For biometric auth, let us make sure we handle the case where the user revokes biometric permission in system settings. Should gracefully fall back to PIN.',
    taskId: 'task_mob_04', authorId: 'user_sam', daysAgo: 1,
  },
];

// ---------------------------------------------------------------------------
// ACTIVITY LOG ENTRIES
// ---------------------------------------------------------------------------

interface ActivitySeed {
  action: string;
  projectId: string;
  taskId: string | null;
  actorId: string;
  details: Record<string, unknown>;
  daysAgo: number;
}

const ACTIVITIES: ActivitySeed[] = [
  // Project creation
  { action: 'project.created', projectId: 'proj_flowboard', taskId: null, actorId: 'user_alex', details: { projectName: 'FlowBoard v2' }, daysAgo: 30 },
  { action: 'project.created', projectId: 'proj_marketing', taskId: null, actorId: 'user_alex', details: { projectName: 'Marketing Site' }, daysAgo: 28 },
  { action: 'project.created', projectId: 'proj_mobile', taskId: null, actorId: 'user_alex', details: { projectName: 'Mobile App' }, daysAgo: 25 },

  // Member additions
  { action: 'member.added', projectId: 'proj_flowboard', taskId: null, actorId: 'user_alex', details: { memberName: 'Sam Chen', role: 'MEMBER' }, daysAgo: 30 },
  { action: 'member.added', projectId: 'proj_flowboard', taskId: null, actorId: 'user_alex', details: { memberName: 'Jordan Blake', role: 'MEMBER' }, daysAgo: 30 },

  // FlowBoard v2 activities
  { action: 'task.created', projectId: 'proj_flowboard', taskId: 'task_fb_13', actorId: 'user_alex', details: { taskTitle: 'Set up project scaffolding with Turborepo' }, daysAgo: 25 },
  { action: 'task.completed', projectId: 'proj_flowboard', taskId: 'task_fb_13', actorId: 'user_alex', details: { taskTitle: 'Set up project scaffolding with Turborepo' }, daysAgo: 14 },
  { action: 'task.created', projectId: 'proj_flowboard', taskId: 'task_fb_14', actorId: 'user_alex', details: { taskTitle: 'Design component library with Tailwind CSS' }, daysAgo: 20 },
  { action: 'task.assigned', projectId: 'proj_flowboard', taskId: 'task_fb_14', actorId: 'user_alex', details: { assigneeName: 'Sam Chen' }, daysAgo: 20 },
  { action: 'task.completed', projectId: 'proj_flowboard', taskId: 'task_fb_14', actorId: 'user_sam', details: { taskTitle: 'Design component library with Tailwind CSS' }, daysAgo: 10 },
  { action: 'task.created', projectId: 'proj_flowboard', taskId: 'task_fb_07', actorId: 'user_alex', details: { taskTitle: 'Implement drag-and-drop for Kanban board' }, daysAgo: 7 },
  { action: 'task.moved', projectId: 'proj_flowboard', taskId: 'task_fb_07', actorId: 'user_alex', details: { from: 'TODO', to: 'IN_PROGRESS' }, daysAgo: 5 },
  { action: 'task.created', projectId: 'proj_flowboard', taskId: 'task_fb_08', actorId: 'user_jordan', details: { taskTitle: 'Fix task creation form validation errors' }, daysAgo: 4 },
  { action: 'task.assigned', projectId: 'proj_flowboard', taskId: 'task_fb_08', actorId: 'user_jordan', details: { assigneeName: 'Sam Chen' }, daysAgo: 4 },
  { action: 'comment.added', projectId: 'proj_flowboard', taskId: 'task_fb_07', actorId: 'user_sam', details: { preview: 'The drag-and-drop is feeling really smooth...' }, daysAgo: 2 },
  { action: 'task.moved', projectId: 'proj_flowboard', taskId: 'task_fb_10', actorId: 'user_sam', details: { from: 'IN_PROGRESS', to: 'IN_REVIEW' }, daysAgo: 1 },
  { action: 'task.moved', projectId: 'proj_flowboard', taskId: 'task_fb_12', actorId: 'user_alex', details: { from: 'IN_PROGRESS', to: 'IN_REVIEW' }, daysAgo: 0 },
  { action: 'comment.added', projectId: 'proj_flowboard', taskId: 'task_fb_12', actorId: 'user_alex', details: { preview: 'The N+1 fix reduced board load time...' }, daysAgo: 0 },

  // Marketing Site activities
  { action: 'task.created', projectId: 'proj_marketing', taskId: 'task_mkt_09', actorId: 'user_alex', details: { taskTitle: 'Design new homepage hero section' }, daysAgo: 18 },
  { action: 'task.completed', projectId: 'proj_marketing', taskId: 'task_mkt_09', actorId: 'user_alex', details: { taskTitle: 'Design new homepage hero section' }, daysAgo: 7 },
  { action: 'task.created', projectId: 'proj_marketing', taskId: 'task_mkt_05', actorId: 'user_alex', details: { taskTitle: 'Build pricing page with tier comparison' }, daysAgo: 5 },
  { action: 'task.moved', projectId: 'proj_marketing', taskId: 'task_mkt_05', actorId: 'user_alex', details: { from: 'TODO', to: 'IN_PROGRESS' }, daysAgo: 3 },
  { action: 'task.created', projectId: 'proj_marketing', taskId: 'task_mkt_06', actorId: 'user_jordan', details: { taskTitle: 'Fix hero section animation jank on mobile' }, daysAgo: 2 },
  { action: 'comment.added', projectId: 'proj_marketing', taskId: 'task_mkt_05', actorId: 'user_jordan', details: { preview: 'The pricing page is looking sharp...' }, daysAgo: 1 },

  // Mobile App activities
  { action: 'task.created', projectId: 'proj_mobile', taskId: 'task_mob_07', actorId: 'user_alex', details: { taskTitle: 'Set up React Native project with Expo' }, daysAgo: 24 },
  { action: 'task.completed', projectId: 'proj_mobile', taskId: 'task_mob_07', actorId: 'user_alex', details: { taskTitle: 'Set up React Native project with Expo' }, daysAgo: 21 },
  { action: 'task.created', projectId: 'proj_mobile', taskId: 'task_mob_04', actorId: 'user_alex', details: { taskTitle: 'Implement biometric authentication flow' }, daysAgo: 8 },
  { action: 'task.moved', projectId: 'proj_mobile', taskId: 'task_mob_04', actorId: 'user_alex', details: { from: 'TODO', to: 'IN_PROGRESS' }, daysAgo: 5 },
  { action: 'task.created', projectId: 'proj_mobile', taskId: 'task_mob_05', actorId: 'user_jordan', details: { taskTitle: 'Fix crash on Android 12 camera permission' }, daysAgo: 3 },
  { action: 'comment.added', projectId: 'proj_mobile', taskId: 'task_mob_05', actorId: 'user_jordan', details: { preview: 'The crash is consistent on Pixel 7...' }, daysAgo: 2 },
  { action: 'task.moved', projectId: 'proj_mobile', taskId: 'task_mob_06', actorId: 'user_jordan', details: { from: 'IN_PROGRESS', to: 'IN_REVIEW' }, daysAgo: 0 },
  { action: 'comment.added', projectId: 'proj_mobile', taskId: 'task_mob_06', actorId: 'user_alex', details: { preview: 'The onboarding animations look fantastic...' }, daysAgo: 0 },
];

// =============================================================================
// MAIN SEED FUNCTION
// =============================================================================

async function main() {
  console.log('Seeding FlowBoard database...\n');

  // -------------------------------------------------------------------------
  // 1. Clear existing data (order matters due to FK constraints)
  // -------------------------------------------------------------------------
  console.log('  Clearing existing data...');
  await prisma.activity.deleteMany();
  await prisma.comment.deleteMany();
  await prisma.taskLabel.deleteMany();
  await prisma.subTask.deleteMany();
  await prisma.task.deleteMany();
  await prisma.label.deleteMany();
  await prisma.projectMember.deleteMany();
  await prisma.project.deleteMany();
  await prisma.user.deleteMany();
  console.log('  Done.\n');

  // -------------------------------------------------------------------------
  // 2. Users
  // -------------------------------------------------------------------------
  console.log('  Creating users...');
  const hashedPassword = await hashPassword(DEMO_PASSWORD);

  for (const u of USERS) {
    await prisma.user.create({
      data: {
        id: u.id,
        email: u.email,
        password: hashedPassword,
        name: u.name,
        avatar: u.avatar,
      },
    });
  }
  console.log(`  Created ${USERS.length} users.\n`);

  // -------------------------------------------------------------------------
  // 3. Projects
  // -------------------------------------------------------------------------
  console.log('  Creating projects...');
  for (const p of PROJECTS) {
    await prisma.project.create({
      data: {
        id: p.id,
        name: p.name,
        description: p.description,
        icon: p.icon,
        color: p.color,
      },
    });
  }
  console.log(`  Created ${PROJECTS.length} projects.\n`);

  // -------------------------------------------------------------------------
  // 4. Project Members
  // -------------------------------------------------------------------------
  console.log('  Adding project members...');
  for (const pm of PROJECT_MEMBERS) {
    await prisma.projectMember.create({
      data: {
        userId: pm.userId,
        projectId: pm.projectId,
        role: pm.role,
      },
    });
  }
  console.log(`  Added ${PROJECT_MEMBERS.length} memberships.\n`);

  // -------------------------------------------------------------------------
  // 5. Labels
  // -------------------------------------------------------------------------
  console.log('  Creating labels...');
  for (const l of LABELS) {
    await prisma.label.create({
      data: {
        id: l.id,
        name: l.name,
        color: l.color,
        projectId: l.projectId,
      },
    });
  }
  console.log(`  Created ${LABELS.length} labels.\n`);

  // -------------------------------------------------------------------------
  // 6. Tasks
  // -------------------------------------------------------------------------
  console.log('  Creating tasks...');
  for (const t of TASKS) {
    await prisma.task.create({
      data: {
        id: t.id,
        title: t.title,
        description: t.description,
        status: t.status,
        priority: t.priority,
        position: t.position,
        projectId: t.projectId,
        creatorId: t.creatorId,
        assigneeId: t.assigneeId,
        dueDate: t.dueDate,
      },
    });
  }
  console.log(`  Created ${TASKS.length} tasks.\n`);

  // -------------------------------------------------------------------------
  // 7. Task-Label associations
  // -------------------------------------------------------------------------
  console.log('  Assigning labels to tasks...');
  let labelCount = 0;
  for (const t of TASKS) {
    for (const labelId of t.labelIds) {
      await prisma.taskLabel.create({
        data: {
          taskId: t.id,
          labelId: labelId,
        },
      });
      labelCount++;
    }
  }
  console.log(`  Created ${labelCount} task-label associations.\n`);

  // -------------------------------------------------------------------------
  // 8. Subtasks
  // -------------------------------------------------------------------------
  console.log('  Creating subtasks...');
  for (const s of SUBTASKS) {
    await prisma.subTask.create({
      data: {
        title: s.title,
        completed: s.completed,
        position: s.position,
        taskId: s.taskId,
      },
    });
  }
  console.log(`  Created ${SUBTASKS.length} subtasks.\n`);

  // -------------------------------------------------------------------------
  // 9. Comments
  // -------------------------------------------------------------------------
  console.log('  Creating comments...');
  for (const c of COMMENTS) {
    const createdAt = daysFromNow(-c.daysAgo);
    await prisma.comment.create({
      data: {
        content: c.content,
        taskId: c.taskId,
        authorId: c.authorId,
        createdAt: createdAt,
      },
    });
  }
  console.log(`  Created ${COMMENTS.length} comments.\n`);

  // -------------------------------------------------------------------------
  // 10. Activity Log
  // -------------------------------------------------------------------------
  console.log('  Creating activity log entries...');
  for (const a of ACTIVITIES) {
    const createdAt = daysFromNow(-a.daysAgo);
    await prisma.activity.create({
      data: {
        action: a.action,
        details: JSON.stringify(a.details),
        projectId: a.projectId,
        taskId: a.taskId,
        actorId: a.actorId,
        createdAt: createdAt,
      },
    });
  }
  console.log(`  Created ${ACTIVITIES.length} activity log entries.\n`);

  // -------------------------------------------------------------------------
  // Summary
  // -------------------------------------------------------------------------
  console.log('='.repeat(60));
  console.log('Seed complete!');
  console.log('='.repeat(60));
  console.log(`  Users:            ${USERS.length}`);
  console.log(`  Projects:         ${PROJECTS.length}`);
  console.log(`  Project Members:  ${PROJECT_MEMBERS.length}`);
  console.log(`  Labels:           ${LABELS.length}`);
  console.log(`  Tasks:            ${TASKS.length}`);
  console.log(`  Task-Labels:      ${labelCount}`);
  console.log(`  Subtasks:         ${SUBTASKS.length}`);
  console.log(`  Comments:         ${COMMENTS.length}`);
  console.log(`  Activity Logs:    ${ACTIVITIES.length}`);
  console.log('');
  console.log('Demo credentials:');
  console.log(`  Email:    alex@flowboard.dev`);
  console.log(`  Password: ${DEMO_PASSWORD}`);
  console.log('');
  console.log('  (Also: sam@flowboard.dev, jordan@flowboard.dev)');
  console.log('='.repeat(60));
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (e) => {
    console.error('Seed failed:', e);
    await prisma.$disconnect();
    process.exit(1);
  });
