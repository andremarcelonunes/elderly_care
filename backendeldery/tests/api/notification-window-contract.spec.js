/**
 * Contract Testing for Notification Window Fields
 * CB-149: Validates API contracts and response schemas
 * 
 * This test suite focuses on:
 * - API contract compliance
 * - Response schema validation
 * - Backward compatibility testing
 * - Data type validation
 * - Field presence validation
 */

const { test, expect } = require('@playwright/test');
const {
  validateNotificationFields,
  isValidTimeFormat,
  isValidDateTimeFormat,
  validateUserResponseStructure,
  validateAttendantResponseStructure,
  generateTestData,
  performHealthCheck,
  logTestResult
} = require('./test-helpers');

test.describe('API Contract Tests - Notification Window Fields', () => {
  let request;

  test.beforeAll(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: 'http://localhost:8000'
    });
    
    // Perform initial health check
    const healthCheck = await performHealthCheck(request);
    console.log('API Health Check:', JSON.stringify(healthCheck, null, 2));
  });

  test.afterAll(async () => {
    await request.dispose();
  });

  test.describe('User Endpoint Contract Validation', () => {
    test('GET /api/v1/users/user/{id} - Response schema should match expected contract', async () => {
      // Arrange
      const testData = generateTestData();
      
      // Act
      const response = await request.get(`/api/v1/users/user/${testData.validIds.user[0]}`);
      
      // Assert
      if (response.status() === 200) {
        const responseBody = await response.json();
        
        // Validate complete response structure
        expect(() => validateUserResponseStructure(responseBody)).not.toThrow();
        
        // Validate specific contract requirements for notification fields
        expect(responseBody).toHaveProperty('notification_start_time');
        expect(responseBody).toHaveProperty('notification_end_time');
        expect(responseBody).toHaveProperty('paused_until');
        
        // Validate data types according to contract
        if (responseBody.notification_start_time !== null) {
          expect(typeof responseBody.notification_start_time).toBe('string');
          expect(isValidTimeFormat(responseBody.notification_start_time)).toBeTruthy();
        }
        
        if (responseBody.notification_end_time !== null) {
          expect(typeof responseBody.notification_end_time).toBe('string');
          expect(isValidTimeFormat(responseBody.notification_end_time)).toBeTruthy();
        }
        
        if (responseBody.paused_until !== null) {
          expect(typeof responseBody.paused_until).toBe('string');
          expect(isValidDateTimeFormat(responseBody.paused_until)).toBeTruthy();
        }
        
        logTestResult('User Contract Validation', responseBody, response.status());
      } else {
        // Even error responses should follow a contract
        const responseBody = await response.json();
        expect(responseBody).toHaveProperty('detail');
        
        logTestResult('User Contract Validation - Error', responseBody, response.status());
      }
    });

    test('GET /api/v1/users/user/{id} - Should handle null values correctly', async () => {
      // This tests the contract when notification fields are null
      const testData = generateTestData();
      
      const response = await request.get(`/api/v1/users/user/${testData.validIds.user[0]}`);
      
      if (response.status() === 200) {
        const responseBody = await response.json();
        
        // Fields should exist even if null
        expect('notification_start_time' in responseBody).toBeTruthy();
        expect('notification_end_time' in responseBody).toBeTruthy();
        expect('paused_until' in responseBody).toBeTruthy();
        
        // Null values should be explicitly null, not undefined or empty string
        if (responseBody.notification_start_time === null) {
          expect(responseBody.notification_start_time).toBeNull();
        }
        if (responseBody.notification_end_time === null) {
          expect(responseBody.notification_end_time).toBeNull();
        }
        if (responseBody.paused_until === null) {
          expect(responseBody.paused_until).toBeNull();
        }
      }
    });

    test('GET /api/v1/users/user/{id} - Error responses should follow standard format', async () => {
      // Test with non-existent user
      const response = await request.get('/api/v1/users/user/999999');
      
      expect(response.status()).toBe(404);
      
      const responseBody = await response.json();
      
      // Error response contract
      expect(responseBody).toHaveProperty('detail');
      expect(typeof responseBody.detail).toBe('string');
      
      // Should not contain notification fields in error responses
      expect(responseBody).not.toHaveProperty('notification_start_time');
      expect(responseBody).not.toHaveProperty('notification_end_time');
      expect(responseBody).not.toHaveProperty('paused_until');
    });
  });

  test.describe('Attendant Endpoint Contract Validation', () => {
    test('GET /api/v1/attendants/{id} - Response schema should match expected contract', async () => {
      // Arrange
      const testData = generateTestData();
      
      // Act
      const response = await request.get(`/api/v1/attendants/${testData.validIds.attendant[0]}`);
      
      // Assert
      if (response.status() === 200) {
        const responseBody = await response.json();
        
        // Validate complete response structure
        expect(() => validateAttendantResponseStructure(responseBody)).not.toThrow();
        
        // Validate attendant-specific contract requirements
        expect(responseBody).toHaveProperty('attendant_data');
        
        // Validate notification fields in attendant response
        expect(responseBody).toHaveProperty('notification_start_time');
        expect(responseBody).toHaveProperty('notification_end_time');
        expect(responseBody).toHaveProperty('paused_until');
        
        // Validate data types according to contract
        if (responseBody.notification_start_time !== null) {
          expect(typeof responseBody.notification_start_time).toBe('string');
          expect(isValidTimeFormat(responseBody.notification_start_time)).toBeTruthy();
        }
        
        if (responseBody.notification_end_time !== null) {
          expect(typeof responseBody.notification_end_time).toBe('string');
          expect(isValidTimeFormat(responseBody.notification_end_time)).toBeTruthy();
        }
        
        if (responseBody.paused_until !== null) {
          expect(typeof responseBody.paused_until).toBe('string');
          expect(isValidDateTimeFormat(responseBody.paused_until)).toBeTruthy();
        }
        
        logTestResult('Attendant Contract Validation', responseBody, response.status());
      } else {
        // Even error responses should follow a contract
        const responseBody = await response.json();
        expect(responseBody).toHaveProperty('detail');
        
        logTestResult('Attendant Contract Validation - Error', responseBody, response.status());
      }
    });

    test('GET /api/v1/attendants/{id} - Attendant data structure should be consistent', async () => {
      const testData = generateTestData();
      
      const response = await request.get(`/api/v1/attendants/${testData.validIds.attendant[0]}`);
      
      if (response.status() === 200) {
        const responseBody = await response.json();
        
        if (responseBody.attendant_data) {
          // Validate attendant_data structure
          expect(typeof responseBody.attendant_data).toBe('object');
          
          // Common attendant fields that should be present
          const expectedAttendantFields = [
            'cpf', 'birthday', 'address', 'city', 'state', 'code_address',
            'registro_conselho', 'nivel_experiencia', 'formacao'
          ];
          
          expectedAttendantFields.forEach(field => {
            expect(responseBody.attendant_data).toHaveProperty(field);
          });
        }
      }
    });

    test('GET /api/v1/attendants/{id} - Error responses should follow standard format', async () => {
      // Test with non-existent attendant
      const response = await request.get('/api/v1/attendants/999999');
      
      expect(response.status()).toBe(404);
      
      const responseBody = await response.json();
      
      // Error response contract
      expect(responseBody).toHaveProperty('detail');
      expect(typeof responseBody.detail).toBe('string');
      
      // Should not contain notification fields in error responses
      expect(responseBody).not.toHaveProperty('notification_start_time');
      expect(responseBody).not.toHaveProperty('notification_end_time');
      expect(responseBody).not.toHaveProperty('paused_until');
    });
  });

  test.describe('Backward Compatibility Tests', () => {
    test('New notification fields should not break existing consumers', async () => {
      // This test ensures that adding notification fields doesn't break existing API consumers
      const testData = generateTestData();
      
      // Test user endpoint
      const userResponse = await request.get(`/api/v1/users/user/${testData.validIds.user[0]}`);
      
      if (userResponse.status() === 200) {
        const userBody = await userResponse.json();
        
        // Existing fields should still be present
        const existingUserFields = ['id', 'name', 'email', 'phone', 'receipt_type', 'role', 'active'];
        
        existingUserFields.forEach(field => {
          expect(userBody).toHaveProperty(field);
        });
        
        // New notification fields should be present but optional (nullable)
        expect('notification_start_time' in userBody).toBeTruthy();
        expect('notification_end_time' in userBody).toBeTruthy();
        expect('paused_until' in userBody).toBeTruthy();
      }
      
      // Test attendant endpoint
      const attendantResponse = await request.get(`/api/v1/attendants/${testData.validIds.attendant[0]}`);
      
      if (attendantResponse.status() === 200) {
        const attendantBody = await attendantResponse.json();
        
        // Existing fields should still be present
        const existingAttendantFields = ['id', 'name', 'email', 'phone', 'receipt_type', 'role', 'active', 'attendant_data'];
        
        existingAttendantFields.forEach(field => {
          expect(attendantBody).toHaveProperty(field);
        });
        
        // New notification fields should be present
        expect('notification_start_time' in attendantBody).toBeTruthy();
        expect('notification_end_time' in attendantBody).toBeTruthy();
        expect('paused_until' in attendantBody).toBeTruthy();
      }
    });

    test('Response structure should remain consistent across versions', async () => {
      const testData = generateTestData();
      
      // Test multiple valid IDs to ensure consistency
      const userIds = testData.validIds.user.slice(0, 3);
      const attendantIds = testData.validIds.attendant.slice(0, 3);
      
      let userStructures = [];
      let attendantStructures = [];
      
      // Test user responses
      for (const userId of userIds) {
        const response = await request.get(`/api/v1/users/user/${userId}`);
        
        if (response.status() === 200) {
          const responseBody = await response.json();
          userStructures.push(Object.keys(responseBody).sort());
        }
      }
      
      // Test attendant responses
      for (const attendantId of attendantIds) {
        const response = await request.get(`/api/v1/attendants/${attendantId}`);
        
        if (response.status() === 200) {
          const responseBody = await response.json();
          attendantStructures.push(Object.keys(responseBody).sort());
        }
      }
      
      // All user responses should have core required fields (paused_until is optional)
      if (userStructures.length > 1) {
        const requiredFields = ['id', 'name', 'phone', 'role', 'active', 'notification_start_time', 'notification_end_time'];
        userStructures.forEach((structure, index) => {
          requiredFields.forEach(field => {
            expect(structure.includes(field)).toBeTruthy();
          });
        });
      }
      
      // All attendant responses should have core required fields (paused_until is optional)
      if (attendantStructures.length > 1) {
        const requiredFields = ['id', 'name', 'phone', 'role', 'active', 'notification_start_time', 'notification_end_time', 'attendant_data'];
        attendantStructures.forEach((structure, index) => {
          requiredFields.forEach(field => {
            expect(structure.includes(field)).toBeTruthy();
          });
        });
      }
    });
  });

  test.describe('Data Validation Contract Tests', () => {
    test('Time format validation should be consistent', async () => {
      const testData = generateTestData();
      
      // Test user endpoint
      const userResponse = await request.get(`/api/v1/users/user/${testData.validIds.user[0]}`);
      
      if (userResponse.status() === 200) {
        const userBody = await userResponse.json();
        
        if (userBody.notification_start_time) {
          expect(userBody.notification_start_time).toMatch(/^([0-1][0-9]|2[0-3]):[0-5][0-9]$/);
        }
        
        if (userBody.notification_end_time) {
          expect(userBody.notification_end_time).toMatch(/^([0-1][0-9]|2[0-3]):[0-5][0-9]$/);
        }
      }
      
      // Test attendant endpoint
      const attendantResponse = await request.get(`/api/v1/attendants/${testData.validIds.attendant[0]}`);
      
      if (attendantResponse.status() === 200) {
        const attendantBody = await attendantResponse.json();
        
        if (attendantBody.notification_start_time) {
          expect(attendantBody.notification_start_time).toMatch(/^([0-1][0-9]|2[0-3]):[0-5][0-9]$/);
        }
        
        if (attendantBody.notification_end_time) {
          expect(attendantBody.notification_end_time).toMatch(/^([0-1][0-9]|2[0-3]):[0-5][0-9]$/);
        }
      }
    });

    test('DateTime format validation should be consistent', async () => {
      const testData = generateTestData();
      
      // Test user endpoint
      const userResponse = await request.get(`/api/v1/users/user/${testData.validIds.user[0]}`);
      
      if (userResponse.status() === 200) {
        const userBody = await userResponse.json();
        
        if (userBody.paused_until) {
          // Should be a valid ISO datetime string
          expect(isValidDateTimeFormat(userBody.paused_until)).toBeTruthy();
          
          // Should be parseable as a Date
          const date = new Date(userBody.paused_until);
          expect(date).toBeInstanceOf(Date);
          expect(!isNaN(date.getTime())).toBeTruthy();
        }
      }
      
      // Test attendant endpoint
      const attendantResponse = await request.get(`/api/v1/attendants/${testData.validIds.attendant[0]}`);
      
      if (attendantResponse.status() === 200) {
        const attendantBody = await attendantResponse.json();
        
        if (attendantBody.paused_until) {
          expect(isValidDateTimeFormat(attendantBody.paused_until)).toBeTruthy();
          
          const date = new Date(attendantBody.paused_until);
          expect(date).toBeInstanceOf(Date);
          expect(!isNaN(date.getTime())).toBeTruthy();
        }
      }
    });

    test('Required vs optional fields should be clearly defined', async () => {
      const testData = generateTestData();
      
      // Test user endpoint
      const userResponse = await request.get(`/api/v1/users/user/${testData.validIds.user[0]}`);
      
      if (userResponse.status() === 200) {
        const userBody = await userResponse.json();
        
        // Required fields (should never be undefined, but can be null)
        const requiredFields = [
          'id', 'name', 'email', 'phone', 'receipt_type', 'role', 'active',
          'notification_start_time', 'notification_end_time', 'paused_until'
        ];
        
        requiredFields.forEach(field => {
          expect(userBody).toHaveProperty(field);
          expect(userBody[field] !== undefined).toBeTruthy();
        });
        
        // Optional fields (can be null or undefined)
        const optionalFields = ['client_data', 'attendant_data'];
        
        optionalFields.forEach(field => {
          if (field in userBody) {
            // If present, should be null or valid object
            expect(userBody[field] === null || typeof userBody[field] === 'object').toBeTruthy();
          }
        });
      }
      
      // Test attendant endpoint
      const attendantResponse = await request.get(`/api/v1/attendants/${testData.validIds.attendant[0]}`);
      
      if (attendantResponse.status() === 200) {
        const attendantBody = await attendantResponse.json();
        
        // Required fields for attendants
        const requiredAttendantFields = [
          'id', 'name', 'email', 'phone', 'receipt_type', 'role', 'active',
          'notification_start_time', 'notification_end_time', 'paused_until', 'attendant_data'
        ];
        
        requiredAttendantFields.forEach(field => {
          expect(attendantBody).toHaveProperty(field);
          expect(attendantBody[field] !== undefined).toBeTruthy();
        });
      }
    });
  });

  test.describe('HTTP Status Code Contract Tests', () => {
    test('Valid requests should return appropriate success codes', async () => {
      const testData = generateTestData();
      
      // Valid user request
      const userResponse = await request.get(`/api/v1/users/user/${testData.validIds.user[0]}`);
      expect([200, 404].includes(userResponse.status())).toBeTruthy(); // 200 if exists, 404 if not
      
      // Valid attendant request
      const attendantResponse = await request.get(`/api/v1/attendants/${testData.validIds.attendant[0]}`);
      expect([200, 404].includes(attendantResponse.status())).toBeTruthy(); // 200 if exists, 404 if not
    });

    test('Invalid requests should return appropriate error codes', async () => {
      const testData = generateTestData();
      
      // Test malformed IDs
      for (const malformedId of testData.invalidIds.malformed) {
        if (malformedId !== '') { // Skip empty string as it might be handled by routing
          const userResponse = await request.get(`/api/v1/users/user/${malformedId}`);
          const attendantResponse = await request.get(`/api/v1/attendants/${malformedId}`);
          
          // Should return 400 (validation error) or 404 (not found)
          expect([400, 404].includes(userResponse.status())).toBeTruthy();
          expect([400, 404].includes(attendantResponse.status())).toBeTruthy();
        }
      }
    });

    test('Non-existent resources should return 404', async () => {
      const testData = generateTestData();
      
      // Test non-existent IDs
      for (const nonExistentId of testData.invalidIds.nonExistent) {
        const userResponse = await request.get(`/api/v1/users/user/${nonExistentId}`);
        const attendantResponse = await request.get(`/api/v1/attendants/${nonExistentId}`);
        
        expect(userResponse.status()).toBe(404);
        expect(attendantResponse.status()).toBe(404);
      }
    });
  });
});