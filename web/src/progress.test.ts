import { describe, expect, it } from 'vitest';
import { completedCount, completionPercent, parseProgress, remainingCost } from './progress';
const tasks = [{ id: 'a' }, { id: 'b' }] as never[];
describe('progress data', () => {
  it('imports only known task IDs and rejects wrong schema versions', () => {
    const result = parseProgress(JSON.stringify({ schemaVersion: 1, completedTaskIds: ['a', 'unknown'], taskNotes: {}, updatedAt: 'now' }), ['a', 'b']);
    expect(result.completedTaskIds).toEqual(['a']);
    expect(result.schemaVersion).toBe(2);
    expect(() => parseProgress('{"schemaVersion":3}', ['a'])).toThrow();
  });
  it('restores only known components and supported statuses', () => {
    const result = parseProgress(JSON.stringify({ schemaVersion: 2, completedTaskIds: [], taskNotes: {}, componentStatuses: { 'HW-1': 'Installed', 'HW-2': 'Invented', unknown: 'Ordered' } }), [], ['HW-1', 'HW-2']);
    expect(result.componentStatuses).toEqual({ 'HW-1': 'Installed' });
  });
  it('calculates task progress and known remaining cost', () => {
    expect(completedCount(tasks, ['a'])).toBe(1);
    expect(completionPercent(tasks, ['a'])).toBe(50);
    expect(remainingCost([{ priceEur: 10, requiredQty: 2, ownedQty: 1 }, { priceEur: null, requiredQty: 1, ownedQty: 0 }])).toBe(10);
  });
});
