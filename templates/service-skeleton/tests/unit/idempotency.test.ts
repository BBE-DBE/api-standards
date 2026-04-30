import { describe, it, expect, vi } from 'vitest';

const mockQuery = vi.fn();
vi.mock('../../src/db.js', () => ({ pool: { query: mockQuery } }));

const { hashRequest } = await import('../../src/lib/idempotency.js');

describe('hashRequest', () => {
  it('order-insensitive on object keys', () => {
    expect(hashRequest({ a: 1, b: 2 })).toEqual(hashRequest({ b: 2, a: 1 }));
  });
  it('arrays are ordered', () => {
    expect(hashRequest([1, 2])).not.toEqual(hashRequest([2, 1]));
  });
});
