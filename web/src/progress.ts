import type { Progress, Task } from './types';

export const STORAGE_KEY = 'tesla-engine-sound-lab.progress';
export const COMPONENT_STATUSES = ['Researching', 'Required', 'Ordered', 'Received', 'Installed', 'Tested', 'Not required', 'Blocked'] as const;
export const blankProgress = (): Progress => ({ schemaVersion: 2, completedTaskIds: [], taskNotes: {}, componentStatuses: {}, updatedAt: new Date().toISOString() });

export function parseProgress(raw: string, validTaskIds: string[], validComponentIds: string[] = []): Progress {
  const parsed: unknown = JSON.parse(raw);
  if (!parsed || typeof parsed !== 'object') throw new Error('Ongeldig back-upbestand.');
  const value = parsed as { schemaVersion?: number; completedTaskIds?: unknown; taskNotes?: unknown; componentStatuses?: unknown; updatedAt?: unknown };
  if (![1, 2].includes(value.schemaVersion ?? 0) || !Array.isArray(value.completedTaskIds) || !value.taskNotes || typeof value.taskNotes !== 'object' || Array.isArray(value.taskNotes)) throw new Error('Niet-ondersteunde voortgangsversie.');
  if (value.schemaVersion === 2 && (!value.componentStatuses || typeof value.componentStatuses !== 'object' || Array.isArray(value.componentStatuses))) throw new Error('Ongeldige materiaalstatussen.');
  const taskNotes = Object.fromEntries(Object.entries(value.taskNotes).filter(([id, note]) => validTaskIds.includes(id) && typeof note === 'string')) as Record<string, string>;
  const componentStatuses = Object.fromEntries(Object.entries(value.componentStatuses ?? {}).filter(([id, status]) => validComponentIds.includes(id) && typeof status === 'string' && COMPONENT_STATUSES.includes(status as typeof COMPONENT_STATUSES[number]))) as Record<string, string>;
  return { schemaVersion: 2, completedTaskIds: [...new Set(value.completedTaskIds.filter((id): id is string => typeof id === 'string' && validTaskIds.includes(id)))], taskNotes, componentStatuses, updatedAt: typeof value.updatedAt === 'string' ? value.updatedAt : new Date().toISOString() };
}

export const completedCount = (tasks: Task[], done: string[]) => tasks.filter(t => done.includes(t.id)).length;
export const completionPercent = (tasks: Task[], done: string[]) => tasks.length ? Math.round(completedCount(tasks, done) * 100 / tasks.length) : 0;
export const remainingCost = (items: { priceEur: number | null; requiredQty: number; ownedQty: number }[]) => items.reduce((sum, item) => sum + (item.priceEur ?? 0) * Math.max(0, item.requiredQty - item.ownedQty), 0);
