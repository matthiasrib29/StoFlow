/**
 * Tests pour TaskPayloadValidator
 */

import { describe, it, expect } from 'vitest';
import { TaskPayloadValidator, TaskValidationError } from '../src/utils/task-validator';
import type { HttpRequestPayload } from '../src/types/http';

describe('TaskPayloadValidator', () => {
  describe('validate()', () => {
    it('devrait valider un payload GET valide', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/v2/users/123',
        method: 'GET'
      };

      expect(() => TaskPayloadValidator.validate(payload)).not.toThrow();
    });

    it('devrait valider un payload POST valide avec body', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/v2/items',
        method: 'POST',
        body: { title: 'Test Item', price: 10 },
        headers: { 'Content-Type': 'application/json' }
      };

      expect(() => TaskPayloadValidator.validate(payload)).not.toThrow();
    });

    it('devrait rejeter un payload sans URL', () => {
      const payload = {
        method: 'GET'
      } as HttpRequestPayload;

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(TaskValidationError);
      expect(() => TaskPayloadValidator.validate(payload)).toThrow('URL manquante');
    });

    it('devrait rejeter une URL invalide', () => {
      const payload: HttpRequestPayload = {
        url: 'not-a-url',
        method: 'GET'
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(TaskValidationError);
    });

    it('devrait rejeter un protocole non-HTTPS', () => {
      const payload: HttpRequestPayload = {
        url: 'http://www.vinted.fr/api/test',
        method: 'GET'
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(TaskValidationError);
      expect(() => TaskPayloadValidator.validate(payload)).toThrow('Protocole non autorisé');
    });

    it('devrait rejeter un domaine non whitelisté', () => {
      const payload: HttpRequestPayload = {
        url: 'https://malicious-site.com/api/test',
        method: 'GET'
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(TaskValidationError);
      expect(() => TaskPayloadValidator.validate(payload)).toThrow('Domaine non autorisé');
    });

    it('devrait accepter api.vinted.fr', () => {
      const payload: HttpRequestPayload = {
        url: 'https://api.vinted.fr/v2/users/123',
        method: 'GET'
      };

      expect(() => TaskPayloadValidator.validate(payload)).not.toThrow();
    });

    it('devrait rejeter une méthode HTTP invalide', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'TRACE' as any
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(TaskValidationError);
      expect(() => TaskPayloadValidator.validate(payload)).toThrow('Méthode HTTP non autorisée');
    });

    it('devrait rejeter un body trop grand', () => {
      const largeBody = 'x'.repeat(2 * 1024 * 1024); // 2MB
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST',
        body: largeBody
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(TaskValidationError);
      expect(() => TaskPayloadValidator.validate(payload)).toThrow('Body trop volumineux');
    });

    it('devrait rejeter un body avec contenu suspect (eval)', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST',
        body: { code: 'eval("alert(1)")' }
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(TaskValidationError);
      expect(() => TaskPayloadValidator.validate(payload)).toThrow('Contenu suspect détecté');
    });

    it('devrait rejeter un body avec script tag', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST',
        body: { html: '<script>alert(1)</script>' }
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(TaskValidationError);
      expect(() => TaskPayloadValidator.validate(payload)).toThrow('Contenu suspect détecté');
    });
  });

  describe('validateSafe()', () => {
    it('devrait retourner true pour un payload valide', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'GET'
      };

      const result = TaskPayloadValidator.validateSafe(payload);

      expect(result).toBe(true);
    });

    it('devrait retourner false pour un payload invalide', () => {
      const payload: HttpRequestPayload = {
        url: 'http://malicious.com/api/test',
        method: 'GET'
      };

      const result = TaskPayloadValidator.validateSafe(payload);

      expect(result).toBe(false);
    });

    it('devrait retourner false sans throw', () => {
      const payload = {
        method: 'GET'
      } as HttpRequestPayload;

      expect(() => TaskPayloadValidator.validateSafe(payload)).not.toThrow();
      expect(TaskPayloadValidator.validateSafe(payload)).toBe(false);
    });
  });

  describe('URL validation via validate()', () => {
    it('devrait accepter une URL Vinted valide', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'GET'
      };

      expect(() => TaskPayloadValidator.validate(payload)).not.toThrow();
    });

    it('devrait accepter api.vinted.fr', () => {
      const payload: HttpRequestPayload = {
        url: 'https://api.vinted.fr/v2/test',
        method: 'GET'
      };

      expect(() => TaskPayloadValidator.validate(payload)).not.toThrow();
    });

    it('devrait rejeter HTTP', () => {
      const payload: HttpRequestPayload = {
        url: 'http://www.vinted.fr/api/test',
        method: 'GET'
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(TaskValidationError);
      expect(() => TaskPayloadValidator.validate(payload)).toThrow('Protocole non autorisé');
    });

    it('devrait rejeter FTP', () => {
      const payload: HttpRequestPayload = {
        url: 'ftp://www.vinted.fr/api/test',
        method: 'GET'
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow('Protocole non autorisé');
    });

    it('devrait rejeter un domaine non whitelisté', () => {
      const payload: HttpRequestPayload = {
        url: 'https://evil.com/api/test',
        method: 'GET'
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow('Domaine non autorisé');
    });
  });

  describe('Method validation via validate()', () => {
    it('devrait accepter GET', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'GET'
      };

      expect(() => TaskPayloadValidator.validate(payload)).not.toThrow();
    });

    it('devrait accepter POST', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST'
      };

      expect(() => TaskPayloadValidator.validate(payload)).not.toThrow();
    });

    it('devrait accepter PUT', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'PUT'
      };

      expect(() => TaskPayloadValidator.validate(payload)).not.toThrow();
    });

    it('devrait accepter DELETE', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'DELETE'
      };

      expect(() => TaskPayloadValidator.validate(payload)).not.toThrow();
    });

    it('devrait accepter PATCH', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'PATCH'
      };

      expect(() => TaskPayloadValidator.validate(payload)).not.toThrow();
    });

    it('devrait rejeter TRACE', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'TRACE' as any
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(
        'Méthode HTTP non autorisée'
      );
    });

    it('devrait rejeter CONNECT', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'CONNECT' as any
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(
        'Méthode HTTP non autorisée'
      );
    });
  });

  describe('Body validation via validate()', () => {
    it('devrait accepter un body de taille raisonnable', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST',
        body: { title: 'Test', description: 'A'.repeat(1000) }
      };

      expect(() => TaskPayloadValidator.validate(payload)).not.toThrow();
    });

    it('devrait rejeter un body trop grand', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST',
        body: 'x'.repeat(2 * 1024 * 1024)
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(
        'Body trop volumineux'
      );
    });

    it('devrait rejeter eval()', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST',
        body: { code: 'eval("malicious")' }
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(
        'Contenu suspect détecté'
      );
    });

    it('devrait rejeter <script>', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST',
        body: { html: '<script>alert(1)</script>' }
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(
        'Contenu suspect détecté'
      );
    });

    it('devrait rejeter javascript:', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST',
        body: { url: 'javascript:alert(1)' }
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(
        'Contenu suspect détecté'
      );
    });

    it('devrait rejeter document.cookie', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST',
        body: { code: 'console.log(document.cookie)' }
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(
        'Contenu suspect détecté'
      );
    });
  });

  describe('Headers validation via validate()', () => {
    it('devrait accepter des headers valides', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      };

      expect(() => TaskPayloadValidator.validate(payload)).not.toThrow();
    });

    it('devrait rejeter plus de 50 headers', () => {
      const headers: Record<string, string> = {};
      for (let i = 0; i < 51; i++) {
        headers[`Header-${i}`] = 'value';
      }

      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST',
        headers
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(
        'Trop de headers'
      );
    });

    it('devrait rejeter un header avec nom trop long', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST',
        headers: {
          ['X-' + 'A'.repeat(300)]: 'value'
        }
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(
        'Nom de header trop long'
      );
    });

    it('devrait rejeter un header avec valeur trop longue', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST',
        headers: {
          'X-Custom': 'value'.repeat(1000)
        }
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(
        'Valeur de header trop longue'
      );
    });
  });

  describe('Files validation via validate()', () => {
    it('devrait accepter un fichier valide', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST',
        files: [{
          field_name: 'photo',
          filename: 'image.jpg',
          content_type: 'image/jpeg',
          data: 'base64data'
        }]
      };

      expect(() => TaskPayloadValidator.validate(payload)).not.toThrow();
    });

    it('devrait rejeter plus de 10 fichiers', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST',
        files: Array(11).fill({
          field_name: 'photo',
          filename: 'image.jpg',
          content_type: 'image/jpeg',
          data: 'data'
        })
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(
        'Trop de fichiers'
      );
    });

    it('devrait rejeter un fichier sans field_name', () => {
      const payload: HttpRequestPayload = {
        url: 'https://www.vinted.fr/api/test',
        method: 'POST',
        files: [{
          filename: 'image.jpg',
          content_type: 'image/jpeg',
          data: 'data'
        }] as any
      };

      expect(() => TaskPayloadValidator.validate(payload)).toThrow(
        'Fichier invalide'
      );
    });
  });
});
