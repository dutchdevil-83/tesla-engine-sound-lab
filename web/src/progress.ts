import type { Progress, Task } from './types';

export const STORAGE_KEY = 'tesla-engine-sound-lab.progress';
export const blankProgress = (): Progress => ({ schemaVersion: 1, completedTaskIds: [], taskNotes: {}, updatedAt: new Date().toISOString() });

export function parseProgress(raw: string, validTaskIds: string[]): Progress {
  const parsed: unknown = JSON.parse(raw);
  if (!parsed || typeof parsed !== 'object') throw new Error('Ongeldig back-upbestand.');
  const value = parsed as Partial<Progress>;
  if (value.schemaVersion !== 1 || !Array.isArray(value.completedTaskIds) || !value.taskNotes || typeof value.taskNotes !== 'object') throw new Error('Niet-ondersteunde voortgangsversie.');
  return { schemaVersion: 1, completedTaskIds: value.completedTaskIds.filter((id): id is string => typeof id === 'string' && validTaskIds.includes(id)), taskNotes: value.taskNotes, updatedAt: typeof value.updatedAt === 'string' ? value.updatedAt : new Date().toISOString() };
}

export const completedCount = (tasks: Task[], done: string[]) => tasks.filter(t => done.includes(t.id)).length;
export const completionPercent = (tasks: Task[], done: string[]) => tasks.length ? Math.round(completedCount(tasks, done) * 100 / tasks.length) : 0;
export const remainingCost = (items: { priceEur: number | null; requiredQty: number; ownedQty: number }[]) => items.reduce((sum, item) => sum + (item.priceEur ?? 0) * Math.max(0, item.requiredQty - item.ownedQty), 0);
