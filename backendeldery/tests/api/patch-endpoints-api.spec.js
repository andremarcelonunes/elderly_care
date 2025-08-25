/**
 * Comprehensive Playwright API Tests for PATCH Endpoints
 * CB-164: Testing partial update functionality for PATCH endpoints
 * 
 * This test suite validates:
 * - PATCH /api/v1/users/update/{user_id} - Partial user updates
 * - PATCH /api/v1/attendants/{user_id} - Partial attendant updates
 * 
 * Test Coverage:
 * - Basic partial update functionality (single/multiple fields)
 * - Notification window fields (notification_start_time, notification_end_time, paused_until)
 * - Validation and error handling (invalid IDs, values, JSON)
 * - Response validation (status codes, schema compliance)
 * - Cross-endpoint consistency (PATCH vs PUT comparison)
 * - Performance and concurrent request handling
 */

const { test, expect } = require('@playwright/test');
const { 
  validateNotificationFields, 
  isValidTimeFormat, 
  isValidDateTimeFormat,
  generateTestData,
  validateUserResponseStructure,
  logTestResult 
} = require('./test-helpers');

// Test data constants - use existing users/attendants from database
const TEST_DATA = {
  validUserId: 1,         // User for testing - ensure this exists
  validUserId2: 26,       // Second user for comparison tests
  validAttendantId: 19,   // Attendant for testing - ensure this exists
  validAttendantId2: 20,  // Second attendant for comparison tests
  nonExistentUserId: 999999,
  nonExistentAttendantId: 999999,
  testUserIdForUpdate: 2, // Dedicated test user for update operations
  testAttendantIdForUpdate: 32 // Dedicated test attendant for update operations
};

// Headers required for PATCH operations
const PATCH_HEADERS = {
  'Content-Type': 'application/json',
  'x-user-id': '1'  // Admin user performing updates
};

test.describe('PATCH User Endpoint Tests (/api/v1/users/update/{user_id})', () => {
  let request;

  test.beforeEach(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: 'http://localhost:8000',
      extraHTTPHeaders: PATCH_HEADERS
    });
  });

  test.afterEach(async () => {
    await request.dispose();
  });

  test.describe('Basic Partial Update Functionality', () => {
    
    test('PATCH user - should update single field (phone)', async () => {
      const updateData = {
        phone: `+55119${Math.floor(Math.random() * 10000000).toString().padStart(7, '0')}`
      };

      const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      const responseBody = await response.json();
      expect(responseBody.phone).toBe(updateData.phone);
      expect(responseBody.id).toBe(TEST_DATA.testUserIdForUpdate);

      // Validate complete response structure
      validateUserResponseStructure(responseBody);
      
      logTestResult('PATCH user - single field update', responseBody, response.status());
    });

    test('PATCH user - should update single field (email)', async () => {
      const timestamp = Date.now();
      const updateData = {
        email: `test.updated.${timestamp}@example.com`
      };

      const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      const responseBody = await response.json();
      expect(responseBody.email).toBe(updateData.email);
      expect(responseBody.id).toBe(TEST_DATA.testUserIdForUpdate);

      validateUserResponseStructure(responseBody);
      
      logTestResult('PATCH user - email update', responseBody, response.status());
    });

    test('PATCH user - should update receipt_type field', async () => {
      const updateData = {
        receipt_type: 2
      };

      const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      const responseBody = await response.json();
      expect(responseBody.receipt_type).toBe(updateData.receipt_type);
      
      validateUserResponseStructure(responseBody);
      
      logTestResult('PATCH user - receipt_type update', responseBody, response.status());
    });

    test('PATCH user - should update multiple fields simultaneously', async () => {
      const timestamp = Date.now();
      const updateData = {
        email: `multi.update.${timestamp}@example.com`,
        receipt_type: 2,
        active: true
      };

      const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      const responseBody = await response.json();
      expect(responseBody.email).toBe(updateData.email);
      expect(responseBody.receipt_type).toBe(updateData.receipt_type);
      expect(responseBody.active).toBe(updateData.active);
      
      validateUserResponseStructure(responseBody);
      
      logTestResult('PATCH user - multiple fields update', responseBody, response.status());
    });

    test('PATCH user - should update receipt_type', async () => {
      const updateData = {
        receipt_type: 3
      };

      const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      const responseBody = await response.json();
      expect(responseBody.receipt_type).toBe(updateData.receipt_type);
      
      validateUserResponseStructure(responseBody);
      
      logTestResult('PATCH user - receipt_type update', responseBody, response.status());
    });

    test('PATCH user - should update active status', async () => {
      const updateData = {
        active: false
      };

      const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      const responseBody = await response.json();
      expect(responseBody.active).toBe(updateData.active);
      
      validateUserResponseStructure(responseBody);
      
      // Revert back to active for future tests
      await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
        data: { active: true }
      });
      
      logTestResult('PATCH user - active status update', responseBody, response.status());
    });

  });

  test.describe('Notification Window Fields Updates', () => {
    
    test('PATCH user - should update notification_start_time', async () => {
      const updateData = {
        notification_start_time: "09:30"
      };

      // Use a user that already has notification fields (user 1)
      const response = await request.patch(`/api/v1/users/update/1`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      // PATCH response may exclude notification fields even when updated
      // Verify the update worked by fetching the user again
      const getResponse = await request.get(`/api/v1/users/user/1`);
      expect(getResponse.status()).toBe(200);
      
      const userData = await getResponse.json();
      expect(userData.notification_start_time).toBe(updateData.notification_start_time);
      expect(isValidTimeFormat(userData.notification_start_time)).toBeTruthy();
      
      validateNotificationFields(userData, updateData.notification_start_time);
      
      logTestResult('PATCH user - notification_start_time update', userData, response.status());
    });

    test('PATCH user - should update notification_end_time', async () => {
      const updateData = {
        notification_end_time: "21:30"
      };

      // Use user 1 that has notification fields
      const response = await request.patch(`/api/v1/users/update/1`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      // Verify the update by fetching the user
      const getResponse = await request.get(`/api/v1/users/user/1`);
      expect(getResponse.status()).toBe(200);
      
      const userData = await getResponse.json();
      expect(userData.notification_end_time).toBe(updateData.notification_end_time);
      expect(isValidTimeFormat(userData.notification_end_time)).toBeTruthy();
      
      validateNotificationFields(userData, null, updateData.notification_end_time);
      
      logTestResult('PATCH user - notification_end_time update', userData, response.status());
    });

    test('PATCH user - should update paused_until', async () => {
      const futureDate = new Date(Date.now() + 24 * 60 * 60 * 1000); // 24 hours from now
      const updateData = {
        paused_until: futureDate.toISOString()
      };

      // Use user 1 that has notification fields
      const response = await request.patch(`/api/v1/users/update/1`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      // Verify the update by fetching the user
      const getResponse = await request.get(`/api/v1/users/user/1`);
      expect(getResponse.status()).toBe(200);
      
      const userData = await getResponse.json();
      expect(userData.paused_until).toBe(updateData.paused_until);
      expect(isValidDateTimeFormat(userData.paused_until)).toBeTruthy();
      
      validateNotificationFields(userData, null, null, updateData.paused_until);
      
      logTestResult('PATCH user - paused_until update', userData, response.status());
    });

    test('PATCH user - should clear paused_until with null', async () => {
      const updateData = {
        paused_until: null
      };

      // Use user 1 that has notification fields
      const response = await request.patch(`/api/v1/users/update/1`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      // Verify the update by fetching the user
      const getResponse = await request.get(`/api/v1/users/user/1`);
      expect(getResponse.status()).toBe(200);
      
      const userData = await getResponse.json();
      expect(userData.paused_until).toBeNull();
      
      logTestResult('PATCH user - paused_until clear', userData, response.status());
    });

    test('PATCH user - should update all notification fields simultaneously', async () => {
      const futureDate = new Date(Date.now() + 48 * 60 * 60 * 1000); // 48 hours from now
      const updateData = {
        notification_start_time: "07:00",
        notification_end_time: "23:00",
        paused_until: futureDate.toISOString()
      };

      // Use user 1 that has notification fields
      const response = await request.patch(`/api/v1/users/update/1`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      // Verify the updates by fetching the user
      const getResponse = await request.get(`/api/v1/users/user/1`);
      expect(getResponse.status()).toBe(200);
      
      const userData = await getResponse.json();
      expect(userData.notification_start_time).toBe(updateData.notification_start_time);
      expect(userData.notification_end_time).toBe(updateData.notification_end_time);
      expect(userData.paused_until).toBe(updateData.paused_until);
      
      validateNotificationFields(
        userData, 
        updateData.notification_start_time, 
        updateData.notification_end_time, 
        updateData.paused_until
      );
      
      logTestResult('PATCH user - all notification fields update', userData, response.status());
    });

  });

  test.describe('Validation and Error Handling', () => {
    
    test('PATCH user - should return 400 for non-existent user', async () => {
      const updateData = {
        email: "should.not.work@example.com"
      };

      const response = await request.patch(`/api/v1/users/update/${TEST_DATA.nonExistentUserId}`, {
        data: updateData
      });

      expect(response.status()).toBe(400);

      const responseBody = await response.json();
      expect(responseBody).toHaveProperty('detail');
      expect(responseBody.detail.toLowerCase()).toContain('not found');
      
      logTestResult('PATCH user - non-existent user', responseBody, response.status());
    });

    test('PATCH user - should handle malformed user IDs', async () => {
      const invalidIds = ['abc', '0', '-1', '1.5', 'null'];
      const updateData = { email: "should.not.work@example.com" };

      for (const invalidId of invalidIds) {
        const response = await request.patch(`/api/v1/users/update/${invalidId}`, {
          data: updateData
        });

        expect([400, 404, 422].includes(response.status())).toBeTruthy();
        
        if (response.status() !== 500) {
          const responseBody = await response.json();
          console.log(`Invalid ID ${invalidId} Response:`, JSON.stringify(responseBody, null, 2));
        }
      }
    });

    test('PATCH user - should validate email format', async () => {
      const updateData = {
        email: "invalid-email-format"
      };

      const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
        data: updateData
      });

      expect([400, 422].includes(response.status())).toBeTruthy();

      const responseBody = await response.json();
      expect(responseBody).toHaveProperty('detail');
      
      logTestResult('PATCH user - invalid email format', responseBody, response.status());
    });

    test('PATCH user - should validate phone format', async () => {
      const invalidPhones = ['invalid-phone', '++5511999999999', 'abc123', '12345678901234567890'];
      
      for (const invalidPhone of invalidPhones) {
        const updateData = {
          phone: invalidPhone
        };

        const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
          data: updateData
        });

        expect([400, 422].includes(response.status())).toBeTruthy();
        
        if (response.status() !== 500) {
          const responseBody = await response.json();
          console.log(`Invalid phone ${invalidPhone} Response:`, JSON.stringify(responseBody, null, 2));
        }
      }
    });

    test('PATCH user - should validate receipt_type values', async () => {
      const invalidReceiptTypes = ['invalid', 'abc', 1.5, 'true', ''];
      
      for (const invalidType of invalidReceiptTypes) {
        const updateData = {
          receipt_type: invalidType
        };

        const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
          data: updateData
        });

        expect([400, 422].includes(response.status())).toBeTruthy();
        
        if (response.status() !== 500) {
          const responseBody = await response.json();
          console.log(`Invalid receipt_type ${invalidType} Response:`, JSON.stringify(responseBody, null, 2));
        }
      }
    });

    test('PATCH user - should validate notification time formats', async () => {
      const invalidTimes = ['24:00', '25:30', '08:60', '8:00', '08:5', 'invalid-time', ''];
      
      for (const invalidTime of invalidTimes) {
        const updateData = {
          notification_start_time: invalidTime
        };

        const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
          data: updateData
        });

        expect([400, 422].includes(response.status())).toBeTruthy();
        
        if (response.status() !== 500) {
          const responseBody = await response.json();
          console.log(`Invalid time ${invalidTime} Response:`, JSON.stringify(responseBody, null, 2));
        }
      }
    });

    test('PATCH user - should validate datetime formats for paused_until', async () => {
      const invalidDateTimes = ['invalid-date', '2024-13-01T10:30:00Z', '2024-02-30T10:30:00Z', '24-12-25 10:30:00'];
      
      for (const invalidDateTime of invalidDateTimes) {
        const updateData = {
          paused_until: invalidDateTime
        };

        const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
          data: updateData
        });

        expect([400, 422].includes(response.status())).toBeTruthy();
        
        if (response.status() !== 500) {
          const responseBody = await response.json();
          console.log(`Invalid datetime ${invalidDateTime} Response:`, JSON.stringify(responseBody, null, 2));
        }
      }
    });

    test('PATCH user - should handle empty request body', async () => {
      const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
        data: {}
      });

      expect(response.status()).toBe(200);  // Empty update should be allowed and return current data

      const responseBody = await response.json();
      expect(responseBody.id).toBe(TEST_DATA.testUserIdForUpdate);
      validateUserResponseStructure(responseBody);
      
      logTestResult('PATCH user - empty request body', responseBody, response.status());
    });

    test('PATCH user - should reject invalid JSON structure', async () => {
      const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
        data: 'invalid-json'
      });

      expect([400, 422].includes(response.status())).toBeTruthy();
      
      logTestResult('PATCH user - invalid JSON', {}, response.status());
    });

    test('PATCH user - should reject name field updates (API contract validation)', async () => {
      const updateData = {
        name: "Name updates not allowed"
      };

      const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
        data: updateData
      });

      expect(response.status()).toBe(400);

      const responseBody = await response.json();
      expect(responseBody).toHaveProperty('detail');
      expect(JSON.stringify(responseBody).toLowerCase()).toContain('not authorized');
      
      logTestResult('PATCH user - name field rejection', responseBody, response.status());
    });

    test('PATCH user - should require x-user-id header', async ({ playwright }) => {
      const requestWithoutHeader = await playwright.request.newContext({
        baseURL: 'http://localhost:8000'
      });

      const updateData = {
        email: "should.require.header@example.com"
      };

      const response = await requestWithoutHeader.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
        data: updateData
      });

      expect([400, 422].includes(response.status())).toBeTruthy();

      await requestWithoutHeader.dispose();
      
      logTestResult('PATCH user - missing x-user-id header', {}, response.status());
    });

  });

});

test.describe('PATCH Attendant Endpoint Tests (/api/v1/attendants/{user_id})', () => {
  let request;

  test.beforeEach(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: 'http://localhost:8000',
      extraHTTPHeaders: PATCH_HEADERS
    });
  });

  test.afterEach(async () => {
    await request.dispose();
  });

  test.describe('Basic Partial Update Functionality', () => {
    
    test('PATCH attendant - should update single field (phone)', async () => {
      const updateData = {
        phone: `+55119${Math.floor(Math.random() * 10000000).toString().padStart(7, '0')}`
      };

      const response = await request.patch(`/api/v1/attendants/${TEST_DATA.testAttendantIdForUpdate}`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      const responseBody = await response.json();
      expect(responseBody.phone).toBe(updateData.phone);
      expect(responseBody.id).toBe(TEST_DATA.testAttendantIdForUpdate);

      validateUserResponseStructure(responseBody);
      
      logTestResult('PATCH attendant - single field update', responseBody, response.status());
    });

    test('PATCH attendant - should update single field (email)', async () => {
      const timestamp = Date.now();
      const updateData = {
        email: `attendant.updated.${timestamp}@example.com`
      };

      const response = await request.patch(`/api/v1/attendants/${TEST_DATA.testAttendantIdForUpdate}`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      const responseBody = await response.json();
      expect(responseBody.email).toBe(updateData.email);
      
      validateUserResponseStructure(responseBody);
      
      logTestResult('PATCH attendant - email update', responseBody, response.status());
    });

    test('PATCH attendant - should update multiple fields simultaneously', async () => {
      const timestamp = Date.now();
      const updateData = {
        email: `multi.attendant.${timestamp}@example.com`,
        receipt_type: 1,
        active: true
      };

      const response = await request.patch(`/api/v1/attendants/${TEST_DATA.testAttendantIdForUpdate}`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      const responseBody = await response.json();
      expect(responseBody.email).toBe(updateData.email);
      expect(responseBody.receipt_type).toBe(updateData.receipt_type);
      expect(responseBody.active).toBe(updateData.active);
      
      validateUserResponseStructure(responseBody);
      
      logTestResult('PATCH attendant - multiple fields update', responseBody, response.status());
    });

  });

  test.describe('Notification Window Fields Updates', () => {
    
    test('PATCH attendant - should update notification_start_time', async () => {
      const updateData = {
        notification_start_time: "08:30"
      };

      const response = await request.patch(`/api/v1/attendants/${TEST_DATA.testAttendantIdForUpdate}`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      const responseBody = await response.json();
      expect(responseBody.notification_start_time).toBe(updateData.notification_start_time);
      expect(isValidTimeFormat(responseBody.notification_start_time)).toBeTruthy();
      
      validateNotificationFields(responseBody, updateData.notification_start_time);
      
      logTestResult('PATCH attendant - notification_start_time update', responseBody, response.status());
    });

    test('PATCH attendant - should update notification_end_time', async () => {
      const updateData = {
        notification_end_time: "19:00"
      };

      const response = await request.patch(`/api/v1/attendants/${TEST_DATA.testAttendantIdForUpdate}`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      const responseBody = await response.json();
      expect(responseBody.notification_end_time).toBe(updateData.notification_end_time);
      expect(isValidTimeFormat(responseBody.notification_end_time)).toBeTruthy();
      
      validateNotificationFields(responseBody, null, updateData.notification_end_time);
      
      logTestResult('PATCH attendant - notification_end_time update', responseBody, response.status());
    });

    test('PATCH attendant - should update paused_until', async () => {
      const futureDate = new Date(Date.now() + 12 * 60 * 60 * 1000); // 12 hours from now
      const updateData = {
        paused_until: futureDate.toISOString()
      };

      const response = await request.patch(`/api/v1/attendants/${TEST_DATA.testAttendantIdForUpdate}`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      const responseBody = await response.json();
      expect(responseBody.paused_until).toBe(updateData.paused_until);
      expect(isValidDateTimeFormat(responseBody.paused_until)).toBeTruthy();
      
      validateNotificationFields(responseBody, null, null, updateData.paused_until);
      
      logTestResult('PATCH attendant - paused_until update', responseBody, response.status());
    });

  });

  test.describe('Validation and Error Handling', () => {
    
    test('PATCH attendant - should return 404 for non-existent attendant', async () => {
      const updateData = {
        email: "should.not.work@example.com"
      };

      const response = await request.patch(`/api/v1/attendants/${TEST_DATA.nonExistentAttendantId}`, {
        data: updateData
      });

      expect(response.status()).toBe(404);

      const responseBody = await response.json();
      expect(responseBody).toHaveProperty('detail');
      expect(responseBody.detail.toLowerCase()).toContain('not found');
      
      logTestResult('PATCH attendant - non-existent attendant', responseBody, response.status());
    });

    test('PATCH attendant - should validate notification time formats', async () => {
      const invalidTimes = ['24:00', '25:30', '08:60', 'invalid-time'];
      
      for (const invalidTime of invalidTimes) {
        const updateData = {
          notification_start_time: invalidTime
        };

        const response = await request.patch(`/api/v1/attendants/${TEST_DATA.testAttendantIdForUpdate}`, {
          data: updateData
        });

        expect([400, 422].includes(response.status())).toBeTruthy();
        
        if (response.status() !== 500) {
          const responseBody = await response.json();
          console.log(`Invalid time ${invalidTime} Response:`, JSON.stringify(responseBody, null, 2));
        }
      }
    });

    test('PATCH attendant - should handle empty request body', async () => {
      const response = await request.patch(`/api/v1/attendants/${TEST_DATA.testAttendantIdForUpdate}`, {
        data: {}
      });

      expect(response.status()).toBe(200);  // Empty update should be allowed

      const responseBody = await response.json();
      expect(responseBody.id).toBe(TEST_DATA.testAttendantIdForUpdate);
      validateUserResponseStructure(responseBody);
      
      logTestResult('PATCH attendant - empty request body', responseBody, response.status());
    });

    test('PATCH attendant - should reject name field updates (API contract validation)', async () => {
      const updateData = {
        name: "Name updates not allowed"
      };

      const response = await request.patch(`/api/v1/attendants/${TEST_DATA.testAttendantIdForUpdate}`, {
        data: updateData
      });

      expect(response.status()).toBe(400);

      const responseBody = await response.json();
      expect(responseBody).toHaveProperty('detail');
      expect(JSON.stringify(responseBody).toLowerCase()).toContain('not authorized');
      
      logTestResult('PATCH attendant - name field rejection', responseBody, response.status());
    });

  });

});

test.describe('Cross-Endpoint Consistency Tests', () => {
  let request;

  test.beforeEach(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: 'http://localhost:8000',
      extraHTTPHeaders: PATCH_HEADERS
    });
  });

  test.afterEach(async () => {
    await request.dispose();
  });

  test('PATCH vs PUT - should produce identical results for same payload', async () => {
    const updateData = {
      email: `consistency.test.${Date.now()}@example.com`,
      notification_start_time: "10:00",
      notification_end_time: "20:00"
    };

    // First, update via PATCH
    const patchResponse = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
      data: updateData
    });
    expect(patchResponse.status()).toBe(200);
    const patchBody = await patchResponse.json();

    // Then, update via PUT with same data
    const putResponse = await request.put(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
      data: updateData
    });
    expect(putResponse.status()).toBe(200);
    const putBody = await putResponse.json();

    // Compare results (excluding timestamps if they differ)
    expect(patchBody.email).toBe(putBody.email);
    expect(patchBody.notification_start_time).toBe(putBody.notification_start_time);
    expect(patchBody.notification_end_time).toBe(putBody.notification_end_time);

    logTestResult('PATCH vs PUT consistency', { patch: patchBody.email, put: putBody.email }, 200);
  });

  test('Response schema consistency - PATCH and PUT should return same structure', async () => {
    const updateData = {
      receipt_type: 3
    };

    // Test PATCH response structure
    const patchResponse = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
      data: updateData
    });
    expect(patchResponse.status()).toBe(200);
    const patchBody = await patchResponse.json();

    // Test PUT response structure
    const putResponse = await request.put(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
      data: updateData
    });
    expect(putResponse.status()).toBe(200);
    const putBody = await putResponse.json();

    // Compare schema structure
    const patchKeys = Object.keys(patchBody).sort();
    const putKeys = Object.keys(putBody).sort();

    expect(patchKeys).toEqual(putKeys);

    // Both should validate against UserResponse schema
    validateUserResponseStructure(patchBody);
    validateUserResponseStructure(putBody);

    logTestResult('Response schema consistency', { patchKeys: patchKeys.length, putKeys: putKeys.length }, 200);
  });

  test('HTTP method semantics - PATCH should allow partial updates', async () => {
    // Get current user data
    const getCurrentResponse = await request.get(`/api/v1/users/user/${TEST_DATA.testUserIdForUpdate}`);
    expect(getCurrentResponse.status()).toBe(200);
    const currentData = await getCurrentResponse.json();

    // Update only one field via PATCH
    const partialUpdateData = {
      active: !currentData.active  // Toggle the active status
    };

    const patchResponse = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
      data: partialUpdateData
    });
    expect(patchResponse.status()).toBe(200);
    const updatedData = await patchResponse.json();

    // Verify only the specified field was updated
    expect(updatedData.active).toBe(partialUpdateData.active);
    expect(updatedData.email).toBe(currentData.email);
    expect(updatedData.phone).toBe(currentData.phone);
    expect(updatedData.receipt_type).toBe(currentData.receipt_type);

    logTestResult('PATCH partial update semantics', updatedData, 200);
  });

});

test.describe('Performance Tests', () => {
  let request;

  test.beforeEach(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: 'http://localhost:8000',
      extraHTTPHeaders: PATCH_HEADERS
    });
  });

  test.afterEach(async () => {
    await request.dispose();
  });

  test('PATCH user - should respond within acceptable time limits', async () => {
    const updateData = {
      receipt_type: 1
    };

    const startTime = Date.now();
    const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
      data: updateData
    });
    const endTime = Date.now();
    const responseTime = endTime - startTime;

    expect(response.status()).toBe(200);
    expect(responseTime).toBeLessThan(3000);  // Should respond within 3 seconds

    console.log(`PATCH user response time: ${responseTime}ms`);
    
    logTestResult('PATCH user performance', {}, response.status(), responseTime);
  });

  test('PATCH attendant - should respond within acceptable time limits', async () => {
    const updateData = {
      receipt_type: 2
    };

    const startTime = Date.now();
    const response = await request.patch(`/api/v1/attendants/${TEST_DATA.testAttendantIdForUpdate}`, {
      data: updateData
    });
    const endTime = Date.now();
    const responseTime = endTime - startTime;

    expect(response.status()).toBe(200);
    expect(responseTime).toBeLessThan(3000);  // Should respond within 3 seconds

    console.log(`PATCH attendant response time: ${responseTime}ms`);
    
    logTestResult('PATCH attendant performance', {}, response.status(), responseTime);
  });

  test('Concurrent PATCH requests - should handle multiple requests', async () => {
    const concurrentRequests = [];
    const numberOfRequests = 3;

    for (let i = 0; i < numberOfRequests; i++) {
      const updateData = {
        receipt_type: (i % 3) + 1  // Cycle between 1, 2, 3
      };
      
      concurrentRequests.push(
        request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
          data: updateData
        })
      );
    }

    const responses = await Promise.all(concurrentRequests);

    // All requests should succeed
    responses.forEach((response, index) => {
      expect(response.status()).toBe(200);
      console.log(`Concurrent request ${index + 1} completed with status ${response.status()}`);
    });

    logTestResult('Concurrent PATCH requests', { count: numberOfRequests }, 200);
  });

});

test.describe('Edge Cases and Boundary Tests', () => {
  let request;

  test.beforeEach(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: 'http://localhost:8000',
      extraHTTPHeaders: PATCH_HEADERS
    });
  });

  test.afterEach(async () => {
    await request.dispose();
  });

  test('PATCH user - should handle boundary time values', async () => {
    const boundaryTimes = [
      { start: "00:00", end: "23:59" },  // Full day
      { start: "12:00", end: "12:01" },  // 1 minute window
      { start: "23:58", end: "23:59" }   // End of day
    ];

    for (const timeSet of boundaryTimes) {
      const updateData = {
        notification_start_time: timeSet.start,
        notification_end_time: timeSet.end
      };

      const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      const responseBody = await response.json();
      expect(responseBody.notification_start_time).toBe(timeSet.start);
      expect(responseBody.notification_end_time).toBe(timeSet.end);

      console.log(`Boundary time test passed: ${timeSet.start} - ${timeSet.end}`);
    }
  });

  test('PATCH user - should handle very long emails within limits', async () => {
    // Create a long but valid email (within reasonable limits)
    const longEmail = `${'a'.repeat(50)}@${'example'.repeat(5)}.com`;
    const updateData = {
      email: longEmail
    };

    const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
      data: updateData
    });

    expect(response.status()).toBe(200);

    const responseBody = await response.json();
    expect(responseBody.email).toBe(longEmail);

    logTestResult('PATCH user - long email', responseBody, response.status());
  });

  test('PATCH user - should reject malformed email addresses', async () => {
    const malformedEmail = 'not-a-valid-email-address';
    const updateData = {
      email: malformedEmail
    };

    const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
      data: updateData
    });

    expect([400, 422].includes(response.status())).toBeTruthy();

    const responseBody = await response.json();
    expect(responseBody).toHaveProperty('detail');
    
    logTestResult('PATCH user - malformed email', responseBody, response.status());
  });

  test('PATCH user - should handle future and past dates for paused_until', async () => {
    const testDates = [
      new Date(Date.now() + 365 * 24 * 60 * 60 * 1000), // 1 year in future
      new Date(Date.now() - 365 * 24 * 60 * 60 * 1000), // 1 year in past
      new Date('2030-12-31T23:59:59Z'), // Specific future date
      new Date('2020-01-01T00:00:00Z')  // Specific past date
    ];

    for (const testDate of testDates) {
      const updateData = {
        paused_until: testDate.toISOString()
      };

      const response = await request.patch(`/api/v1/users/update/${TEST_DATA.testUserIdForUpdate}`, {
        data: updateData
      });

      expect(response.status()).toBe(200);

      const responseBody = await response.json();
      expect(responseBody.paused_until).toBe(updateData.paused_until);
      expect(isValidDateTimeFormat(responseBody.paused_until)).toBeTruthy();

      console.log(`Date test passed: ${testDate.toISOString()}`);
    }
  });

});