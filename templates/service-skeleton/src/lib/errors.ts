// Cross-service error codes. Authoritative registry:
// `api-standards/protocols/error-codes.yaml`.

export type ErrorCode =
  | 'unauthorized'
  | 'forbidden'
  | 'not_found'
  | 'conflict'
  | 'invalid_input'
  | 'idempotency_mismatch'
  | 'too_many_failed_auth'
  | 'internal';

export class AppError extends Error {
  override readonly name = 'AppError';
  constructor(
    readonly code: ErrorCode,
    readonly status: number,
    message: string,
    readonly details?: Record<string, unknown>,
  ) { super(message); }
  toJSON() {
    return { error: { code: this.code, message: this.message, details: this.details ?? null } };
  }
}

export const Unauthorized      = (m = 'missing or invalid token') => new AppError('unauthorized',      401, m);
export const Forbidden         = (m = 'forbidden')                  => new AppError('forbidden',         403, m);
export const NotFound          = (m = 'not found')                  => new AppError('not_found',         404, m);
export const Conflict          = (m: string, d?: Record<string, unknown>) => new AppError('conflict',          409, m, d);
export const InvalidInput      = (m: string, d?: Record<string, unknown>) => new AppError('invalid_input',     422, m, d);
export const IdempotencyMismatch = (m = 'Idempotency-Key already used with different body') =>
  new AppError('idempotency_mismatch', 409, m);
