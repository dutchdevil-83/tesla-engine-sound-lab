import type { Progress, Task } from './types';

export const STORAGE_KEY = 'tesla-engine-sound-lab.progress';
export const COMPONENT_STATUSES = ['Researching', 'Required', 'Ordered', 'Received', 'Installed', 'Tested', 'Not required', 'Blocked'] as const;
export const blankProgress = (): Progress => ({ schemaVersion: 3, completedTaskIds: [], taskNotes: {}, componentStatuses: {}, componentDetails: {}, speakerMatrix: {}, updatedAt: new Date().toISOString() });

export function parseProgress(raw: string, validTaskIds: string[], validComponentIds: string[] = []): Progress {
  const parsed: unknown = JSON.parse(raw);
  if (!parsed || typeof parsed !== 'object') throw new Error('Ongeldig back-upbestand.');
  const value = parsed as { schemaVersion?: number; completedTaskIds?: unknown; taskNotes?: unknown; componentStatuses?: unknown; componentDetails?: unknown; speakerMatrix?: unknown; updatedAt?: unknown };
  if (![1, 2, 3].includes(value.schemaVersion ?? 0) || !Array.isArray(value.completedTaskIds) || !value.taskNotes || typeof value.taskNotes !== 'object' || Array.isArray(value.taskNotes)) throw new Error('Niet-ondersteunde voortgangsversie.');
  if ((value.schemaVersion ?? 0) >= 2 && (!value.componentStatuses || typeof value.componentStatuses !== 'object' || Array.isArray(value.componentStatuses))) throw new Error('Ongeldige materiaalstatussen.');
  if (value.schemaVersion === 3 && (!value.componentDetails || typeof value.componentDetails !== 'object' || Array.isArray(value.componentDetails) || !value.speakerMatrix || typeof value.speakerMatrix !== 'object' || Array.isArray(value.speakerMatrix))) throw new Error('Ongeldige materiaalgegevens of luidsprekermatrix.');
  const taskNotes = Object.fromEntries(Object.entries(value.taskNotes).filter(([id, note]) => validTaskIds.includes(id) && typeof note === 'string')) as Record<string, string>;
  const componentStatuses = Object.fromEntries(Object.entries(value.componentStatuses ?? {}).filter(([id, status]) => validComponentIds.includes(id) && typeof status === 'string' && COMPONENT_STATUSES.includes(status as typeof COMPONENT_STATUSES[number]))) as Record<string, string>;
  const componentDetails: Progress['componentDetails'] = {};
  for (const [id, raw] of Object.entries(value.componentDetails ?? {})) {
    if (!validComponentIds.includes(id) || !raw || typeof raw !== 'object' || Array.isArray(raw)) continue;
    const d = raw as Record<string, unknown>;
    const clean: Progress['componentDetails'][string] = {};
    if (typeof d.ownedQty === 'number' && Number.isInteger(d.ownedQty) && d.ownedQty >= 0) clean.ownedQty = d.ownedQty;
    if (d.priceEur === null || (typeof d.priceEur === 'number' && Number.isFinite(d.priceEur) && d.priceEur >= 0)) clean.priceEur = d.priceEur;
    if (typeof d.supplier === 'string') clean.supplier = d.supplier;
    if (typeof d.priceVerified === 'string') clean.priceVerified = d.priceVerified;
    componentDetails[id] = clean;
  }
  const speakerMatrix = Object.fromEntries(Object.entries(value.speakerMatrix ?? {}).filter(([, v]) => Array.isArray(v) && v.length === 6 && v.every(x => typeof x === 'string'))) as Record<string, string[]>;
  return { schemaVersion: 3, completedTaskIds: [...new Set(value.completedTaskIds.filter((id): id is string => typeof id === 'string' && validTaskIds.includes(id)))], taskNotes, componentStatuses, componentDetails, speakerMatrix, updatedAt: typeof value.updatedAt === 'string' ? value.updatedAt : new Date().toISOString() };
}

export const completedCount = (tasks: Task[], done: string[]) => tasks.filter(t => done.includes(t.id)).length;
export const completionPercent = (tasks: Task[], done: string[]) => tasks.length ? Math.round(completedCount(tasks, done) * 100 / tasks.length) : 0;
export const remainingCost = (items: { priceEur: number | null; requiredQty: number; ownedQty: number; status?: string }[]) => items.reduce((sum, item) => sum + (item.status === 'Not required' ? 0 : (item.priceEur ?? 0) * Math.max(0, item.requiredQty - item.ownedQty)), 0);
export function csvCell(value: unknown): string {
  let text = String(value ?? '');
  if (/^[\t\r\n ]*[=+\-@]/.test(text)) text = `'${text}`;
  return `"${text.replaceAll('"', '""')}"`;
}
