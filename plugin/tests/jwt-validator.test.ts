/**
 * Tests pour JWTValidator
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { JWTValidator, JWTValidationError } from '../src/utils/jwt-validator';

describe('JWTValidator', () => {
  describe('validate()', () => {
    it('devrait valider un token JWT valide', () => {
      // Token JWT valide (header.payload.signature)
      // Payload: {"user_id": 123, "exp": Date.now()/1000 + 3600, "role": "user"}
      const futureExp = Math.floor(Date.now() / 1000) + 3600;
      const payload = btoa(JSON.stringify({ user_id: 123, exp: futureExp, role: 'user' }));
      const token = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.${payload}.signature`;

      const result = JWTValidator.validate(token);

      expect(result).toEqual({ user_id: 123, exp: futureExp, role: 'user' });
    });

    it('devrait rejeter un token avec structure invalide', () => {
      expect(() => JWTValidator.validate('invalid.token')).toThrow(JWTValidationError);
      expect(() => JWTValidator.validate('only.two.parts')).toThrow(JWTValidationError);
      expect(() => JWTValidator.validate('')).toThrow(JWTValidationError);
    });

    it('devrait rejeter un token avec payload invalide', () => {
      const invalidPayload = btoa('not-json');
      const token = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.${invalidPayload}.signature`;

      expect(() => JWTValidator.validate(token)).toThrow(JWTValidationError);
    });

    it('devrait rejeter un token expiré', () => {
      const pastExp = Math.floor(Date.now() / 1000) - 3600; // Expiré il y a 1h
      const payload = btoa(JSON.stringify({ user_id: 123, exp: pastExp }));
      const token = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.${payload}.signature`;

      expect(() => JWTValidator.validate(token)).toThrow(JWTValidationError);
      expect(() => JWTValidator.validate(token)).toThrow('Token JWT expiré');
    });

    it('devrait rejeter un token sans user_id', () => {
      const futureExp = Math.floor(Date.now() / 1000) + 3600;
      const payload = btoa(JSON.stringify({ exp: futureExp })); // Manque user_id
      const token = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.${payload}.signature`;

      expect(() => JWTValidator.validate(token)).toThrow(JWTValidationError);
    });

    it('devrait rejeter un token sans exp', () => {
      const payload = btoa(JSON.stringify({ user_id: 123 })); // Manque exp
      const token = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.${payload}.signature`;

      expect(() => JWTValidator.validate(token)).toThrow(JWTValidationError);
    });
  });

  describe('validateSafe()', () => {
    it('devrait retourner le payload pour un token valide', () => {
      const futureExp = Math.floor(Date.now() / 1000) + 3600;
      const payload = btoa(JSON.stringify({ user_id: 123, exp: futureExp, role: 'user' }));
      const token = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.${payload}.signature`;

      const result = JWTValidator.validateSafe(token);

      expect(result).toEqual({ user_id: 123, exp: futureExp, role: 'user' });
    });

    it('devrait retourner null pour un token invalide', () => {
      const result = JWTValidator.validateSafe('invalid-token');

      expect(result).toBeNull();
    });

    it('devrait retourner null pour un token expiré', () => {
      const pastExp = Math.floor(Date.now() / 1000) - 3600;
      const payload = btoa(JSON.stringify({ user_id: 123, exp: pastExp }));
      const token = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.${payload}.signature`;

      const result = JWTValidator.validateSafe(token);

      expect(result).toBeNull();
    });
  });

  describe('isExpiringSoon()', () => {
    it('devrait retourner true si le token expire bientôt', () => {
      const soonExp = Math.floor(Date.now() / 1000) + 120; // Expire dans 2 minutes
      const payload = { user_id: 123, exp: soonExp, role: 'user' };

      const result = JWTValidator.isExpiringSoon(payload, 300); // Threshold 5 minutes

      expect(result).toBe(true);
    });

    it('devrait retourner false si le token n\'expire pas bientôt', () => {
      const futureExp = Math.floor(Date.now() / 1000) + 3600; // Expire dans 1h
      const payload = { user_id: 123, exp: futureExp, role: 'user' };

      const result = JWTValidator.isExpiringSoon(payload, 300); // Threshold 5 minutes

      expect(result).toBe(false);
    });

    it('devrait retourner false pour un token déjà expiré', () => {
      const pastExp = Math.floor(Date.now() / 1000) - 3600; // Expiré il y a 1h
      const payload = { user_id: 123, exp: pastExp, role: 'user' };

      const result = JWTValidator.isExpiringSoon(payload, 300);

      expect(result).toBe(false);
    });

    it('devrait utiliser le threshold par défaut (300s)', () => {
      const soonExp = Math.floor(Date.now() / 1000) + 120; // Expire dans 2 minutes
      const payload = { user_id: 123, exp: soonExp, role: 'user' };

      const result = JWTValidator.isExpiringSoon(payload);

      expect(result).toBe(true);
    });
  });

  describe('getTimeUntilExpiration()', () => {
    it('devrait retourner le temps restant en secondes', () => {
      const futureExp = Math.floor(Date.now() / 1000) + 600; // Expire dans 10 minutes
      const payload = { user_id: 123, exp: futureExp };

      const result = JWTValidator.getTimeUntilExpiration(payload);

      expect(result).toBeGreaterThanOrEqual(595);
      expect(result).toBeLessThanOrEqual(600);
    });

    it('devrait retourner 0 pour un token expiré', () => {
      const pastExp = Math.floor(Date.now() / 1000) - 600;
      const payload = { user_id: 123, exp: pastExp };

      const result = JWTValidator.getTimeUntilExpiration(payload);

      expect(result).toBe(0);
    });
  });

  describe('formatTimeRemaining()', () => {
    it('devrait formater le temps restant en minutes', () => {
      const futureExp = Math.floor(Date.now() / 1000) + 180; // 3 minutes
      const payload = { user_id: 123, exp: futureExp, role: 'user' };

      const result = JWTValidator.formatTimeRemaining(payload);

      expect(result).toMatch(/\dm \ds/); // Format "Xm Ys"
    });

    it('devrait formater le temps restant en heures', () => {
      const futureExp = Math.floor(Date.now() / 1000) + 7200; // 2 heures
      const payload = { user_id: 123, exp: futureExp, role: 'user' };

      const result = JWTValidator.formatTimeRemaining(payload);

      expect(result).toContain('h');
    });

    it('devrait retourner "Expiré" pour un token expiré', () => {
      const pastExp = Math.floor(Date.now() / 1000) - 600;
      const payload = { user_id: 123, exp: pastExp, role: 'user' };

      const result = JWTValidator.formatTimeRemaining(payload);

      expect(result).toBe('Expiré');
    });
  });

  describe('hasValidStructure()', () => {
    it('devrait valider un token avec 3 parties', () => {
      const token = 'header.payload.signature';

      const result = JWTValidator.hasValidStructure(token);

      expect(result).toBe(true);
    });

    it('devrait rejeter un token avec 2 parties', () => {
      const token = 'header.payload';

      const result = JWTValidator.hasValidStructure(token);

      expect(result).toBe(false);
    });

    it('devrait rejeter une chaîne vide', () => {
      const result = JWTValidator.hasValidStructure('');

      expect(result).toBe(false);
    });
  });

  describe('decodePayload()', () => {
    it('devrait décoder un payload valide', () => {
      const originalPayload = { user_id: 123, exp: 1234567890 };
      const encoded = btoa(JSON.stringify(originalPayload));
      const token = `header.${encoded}.signature`;

      const result = JWTValidator.decodePayload(token);

      expect(result).toEqual(originalPayload);
    });

    it('devrait rejeter un payload non-JSON', () => {
      const invalidPayload = btoa('not-json');
      const token = `header.${invalidPayload}.signature`;

      expect(() => JWTValidator.decodePayload(token)).toThrow(JWTValidationError);
    });
  });

  describe('isNotExpired()', () => {
    it('devrait retourner true pour un token non expiré', () => {
      const futureExp = Math.floor(Date.now() / 1000) + 3600;
      const payload = { user_id: 123, exp: futureExp };

      const result = JWTValidator.isNotExpired(payload);

      expect(result).toBe(true);
    });

    it('devrait retourner false pour un token expiré', () => {
      const pastExp = Math.floor(Date.now() / 1000) - 3600;
      const payload = { user_id: 123, exp: pastExp };

      const result = JWTValidator.isNotExpired(payload);

      expect(result).toBe(false);
    });

    it('devrait retourner false pour un token expirant maintenant', () => {
      const nowExp = Math.floor(Date.now() / 1000);
      const payload = { user_id: 123, exp: nowExp };

      const result = JWTValidator.isNotExpired(payload);

      expect(result).toBe(false);
    });
  });
});
