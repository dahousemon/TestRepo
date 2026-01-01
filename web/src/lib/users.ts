import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';
import crypto from 'crypto';
import { getAllPeaks } from './peaks';

interface User {
  id: string;
  email: string;
  name: string;
  passwordHash: string;
  createdAt: string;
}

interface Summit {
  id: string;
  odlerId: string;
  peakId: string;
  summitDate: string | null;
  notes: string | null;
  createdAt: string;
}

interface Database {
  users: User[];
  summits: Summit[];
}

const DB_PATH = join(process.cwd(), 'data', 'db.json');

function ensureDbExists(): void {
  const dataDir = join(process.cwd(), 'data');
  if (!existsSync(dataDir)) {
    mkdirSync(dataDir, { recursive: true });
  }
  if (!existsSync(DB_PATH)) {
    writeFileSync(DB_PATH, JSON.stringify({ users: [], summits: [] }, null, 2));
  }
}

function readDb(): Database {
  ensureDbExists();
  const data = readFileSync(DB_PATH, 'utf-8');
  return JSON.parse(data);
}

function writeDb(db: Database): void {
  ensureDbExists();
  writeFileSync(DB_PATH, JSON.stringify(db, null, 2));
}

// Simple password hashing (use bcrypt in production)
function hashPassword(password: string): string {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.pbkdf2Sync(password, salt, 1000, 64, 'sha512').toString('hex');
  return `${salt}:${hash}`;
}

export function verifyPassword(password: string, storedHash: string): boolean {
  const [salt, hash] = storedHash.split(':');
  const verifyHash = crypto.pbkdf2Sync(password, salt, 1000, 64, 'sha512').toString('hex');
  return hash === verifyHash;
}

export function getUserByEmail(email: string): User | undefined {
  const db = readDb();
  return db.users.find(u => u.email.toLowerCase() === email.toLowerCase());
}

export function getUserById(id: string): User | undefined {
  const db = readDb();
  return db.users.find(u => u.id === id);
}

export function createUser(email: string, password: string, name: string): User {
  const db = readDb();

  const user: User = {
    id: crypto.randomUUID(),
    email: email.toLowerCase(),
    name,
    passwordHash: hashPassword(password),
    createdAt: new Date().toISOString(),
  };

  db.users.push(user);
  writeDb(db);

  return user;
}

// Summit operations
export function getUserSummits(userId: string): Summit[] {
  const db = readDb();
  return db.summits.filter(s => s.odlerId === userId);
}

export function addSummit(userId: string, peakId: string, summitDate?: string, notes?: string): Summit {
  const db = readDb();

  // Check if already summited
  const existing = db.summits.find(s => s.odlerId === userId && s.peakId === peakId);
  if (existing) {
    throw new Error('Peak already summited');
  }

  const summit: Summit = {
    id: crypto.randomUUID(),
    odlerId: userId,
    peakId,
    summitDate: summitDate || null,
    notes: notes || null,
    createdAt: new Date().toISOString(),
  };

  db.summits.push(summit);
  writeDb(db);

  return summit;
}

export function removeSummit(userId: string, peakId: string): boolean {
  const db = readDb();
  const index = db.summits.findIndex(s => s.odlerId === userId && s.peakId === peakId);

  if (index === -1) {
    return false;
  }

  db.summits.splice(index, 1);
  writeDb(db);

  return true;
}

export function hasSummited(userId: string, peakId: string): boolean {
  const db = readDb();
  return db.summits.some(s => s.odlerId === userId && s.peakId === peakId);
}

export function getUserStats(userId: string) {
  const summits = getUserSummits(userId);
  const allPeaks = getAllPeaks();

  const summitedPeakIds = new Set(summits.map(s => s.peakId));
  const summitedPeaks = allPeaks.filter((p: { id: string }) => summitedPeakIds.has(p.id));

  const fourteeners = summitedPeaks.filter((p: { elevation: number }) => p.elevation >= 14000);
  const thirteeners = summitedPeaks.filter((p: { elevation: number }) => p.elevation >= 13000 && p.elevation < 14000);
  const totalElevation = summitedPeaks.reduce((sum: number, p: { elevation: number }) => sum + p.elevation, 0);

  return {
    totalSummited: summits.length,
    fourteenersSummited: fourteeners.length,
    thirteenersSummited: thirteeners.length,
    totalElevationGained: totalElevation,
    percentComplete: Math.round((summits.length / 200) * 100),
  };
}
