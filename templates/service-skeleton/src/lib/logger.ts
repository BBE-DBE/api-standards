import pino from 'pino';
import { config } from '../config.js';

const baseOptions = {
  level: config.LOG_LEVEL,
  base: { service: '__SERVICE_NAME__', env: config.NODE_ENV },
  timestamp: pino.stdTimeFunctions.isoTime,
  redact: {
    paths: [
      'req.headers.authorization',
      'req.headers["x-api-key"]',
      '*.password',
      '*.token',
    ],
    censor: '[REDACTED]',
  },
};

export const logger = config.NODE_ENV === 'development'
  ? pino({
      ...baseOptions,
      transport: {
        target: 'pino-pretty',
        options: { colorize: true, translateTime: 'SYS:standard', ignore: 'pid,hostname,service,env' },
      },
    })
  : pino(baseOptions);
