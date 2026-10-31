import { describe, expect, it } from 'vitest';
import { completedCount, completionPercent, parseProgress, remainingCost } from './progress';
const tasks = [{ id: 'a' }, { id: 'b' }] as never[];
describe('progress data', () => {
  it('imports only known task IDs and rejects wrong schema versions', () => {
    const result = parseProgress(JSON.stringify({ schemaVersion: 1, completedTaskIds: ['a', 'unknown'], taskNotes: {}, updatedAt: 'now' }), ['a', 'b']);
    expect(result.completedTaskIds).toEqual(['a']);
    expect(() => parseProgress('{"schemaVersion":2}', ['a'])).toThrow();
  });
  it('calculates task progress and known remaining cost', () => {
    expect(completedCount(tasks, ['a'])).toBe(1);
    expect(completionPercent(tasks, ['a'])).toBe(50);
    expect(remainingCost([{ priceEur: 10, requiredQty: 2, ownedQty: 1 }, { priceEur: null, requiredQty: 1, ownedQty: 0 }])).toBe(10);
  });
});
