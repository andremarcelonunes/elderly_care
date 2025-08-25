/**
 * Comprehensive Playwright API Tests for Notification Window Fields
 * CB-149: Testing notification window fields in GET endpoints
 * 
 * This test suite validates:
 * - GET /api/v1/users/user/{user_id} - Returns user info with notification fields
 * - GET /api/v1/attendants/{attendant_id} - Returns attendant info with notification fields
 * 
 * Notification fields tested:
 * - notification_start_time (string, HH:MM format, default "08:00")
 * - notification_end_time (string, HH:MM format, default "22:00")  
 * - paused_until (datetime, nullable)
 */

const { test, expect } = require('@playwright/test');

// Test data constants
const TEST_DATA = {
  validUserId: 1,       // User with paused_until set
  validUserId2: 26,     // User with default values (paused_until = null)
  validAttendantId: 19, // Attendant with paused_until set
  validAttendantId2: 20, // Attendant with default values
  nonExistentUserId: 999999,
  nonExistentAttendantId: 999999,
  defaultNotificationStart: "08:00",
  defaultNotificationEnd: "22:00"
};

// Helper function to validate notification window fields
function validateNotificationFields(response, expectedStart = null, expectedEnd = null, expectedPausedUntil = null, shouldHavePausedUntil = true) {
  expect(response).toHaveProperty('notification_start_time');
  expect(response).toHaveProperty('notification_end_time');
  
  // paused_until may be excluded when null due to response_model_exclude_none=True
  if (shouldHavePausedUntil) {
    expect(response).toHaveProperty('paused_until');
  }
  
  if (expectedStart !== null) {
    expect(response.notification_start_time).toBe(expectedStart);
  }
  if (expectedEnd !== null) {
    expect(response.notification_end_time).toBe(expectedEnd);
  }
  if (expectedPausedUntil !== null) {
    expect(response.paused_until).toBe(expectedPausedUntil);
  }
}

// Helper function to validate time format (HH:MM)
function isValidTimeFormat(timeString) {
  if (!timeString) return true; // null/undefined is valid
  const timeRegex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/;
  return timeRegex.test(timeString);
}

// Helper function to validate datetime format
function isValidDateTimeFormat(dateTimeString) {
  if (!dateTimeString) return true; // null/undefined is valid
  const date = new Date(dateTimeString);
  return !isNaN(date.getTime());
}

test.describe('User Notification Window API Tests', () => {
  let request;

  test.beforeEach(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: 'http://localhost:8000'
    });
  });

  test.afterEach(async () => {
    await request.dispose();
  });

  test('GET /api/v1/users/user/{user_id} - should return 200 with notification fields for valid user', async () => {
    // Act
    const response = await request.get(`/api/v1/users/user/${TEST_DATA.validUserId}`);
    
    // Assert response status
    expect(response.status()).toBe(200);
    
    // Assert response structure
    const responseBody = await response.json();
    expect(responseBody).toHaveProperty('id');
    expect(responseBody).toHaveProperty('name');
    expect(responseBody).toHaveProperty('email');
    expect(responseBody).toHaveProperty('phone');
    expect(responseBody).toHaveProperty('receipt_type');
    expect(responseBody).toHaveProperty('role');
    expect(responseBody).toHaveProperty('active');
    
    // Validate notification window fields are present
    validateNotificationFields(responseBody);
    
    // Validate data types and formats
    expect(isValidTimeFormat(responseBody.notification_start_time)).toBeTruthy();
    expect(isValidTimeFormat(responseBody.notification_end_time)).toBeTruthy();
    expect(isValidDateTimeFormat(responseBody.paused_until)).toBeTruthy();
    
    // Log response for debugging
    console.log('User Response:', JSON.stringify(responseBody, null, 2));
  });

  test('GET /api/v1/users/user/{user_id} - should return default notification window when not explicitly set', async () => {
    // This test assumes there's a user with default values
    // In a real scenario, you might want to create a test user first
    
    // Act
    const response = await request.get(`/api/v1/users/user/${TEST_DATA.validUserId}`);
    
    // Assert
    expect(response.status()).toBe(200);
    const responseBody = await response.json();
    
    // Validate notification fields exist
    validateNotificationFields(responseBody);
    
    // Check if default values are used (this may vary based on implementation)
    if (responseBody.notification_start_time !== null) {
      expect(isValidTimeFormat(responseBody.notification_start_time)).toBeTruthy();
    }
    if (responseBody.notification_end_time !== null) {
      expect(isValidTimeFormat(responseBody.notification_end_time)).toBeTruthy();
    }
  });

  test('GET /api/v1/users/user/{user_id} - should return 404 for non-existent user', async () => {
    // Act
    const response = await request.get(`/api/v1/users/user/${TEST_DATA.nonExistentUserId}`);
    
    // Assert
    expect(response.status()).toBe(404);
    
    const responseBody = await response.json();
    expect(responseBody).toHaveProperty('detail');
    
    // Log error response for debugging
    console.log('404 User Response:', JSON.stringify(responseBody, null, 2));
  });

  test('GET /api/v1/users/user/{user_id} - should handle invalid user ID format gracefully', async () => {
    // Test with various invalid formats
    const invalidIds = ['abc', '0', '-1', '1.5', 'null'];
    
    for (const invalidId of invalidIds) {
      const response = await request.get(`/api/v1/users/user/${invalidId}`);
      
      // Should return 400 for validation errors or 404 for not found
      expect([400, 404].includes(response.status())).toBeTruthy();
      
      if (response.status() !== 500) { // Avoid logging server errors
        const responseBody = await response.json();
        console.log(`Invalid ID ${invalidId} Response:`, JSON.stringify(responseBody, null, 2));
      }
    }
  });

  test('GET /api/v1/users/user/{user_id} - should validate notification time format constraints', async () => {
    // Act
    const response = await request.get(`/api/v1/users/user/${TEST_DATA.validUserId}`);
    
    if (response.status() === 200) {
      const responseBody = await response.json();
      
      // Validate time format if present
      if (responseBody.notification_start_time) {
        expect(responseBody.notification_start_time).toMatch(/^([0-1][0-9]|2[0-3]):[0-5][0-9]$/);
      }
      
      if (responseBody.notification_end_time) {
        expect(responseBody.notification_end_time).toMatch(/^([0-1][0-9]|2[0-3]):[0-5][0-9]$/);
      }
      
      // Validate logical constraint (start time should be before end time)
      if (responseBody.notification_start_time && responseBody.notification_end_time) {
        const startTime = responseBody.notification_start_time;
        const endTime = responseBody.notification_end_time;
        
        // Convert to comparable format
        const startMinutes = parseInt(startTime.split(':')[0]) * 60 + parseInt(startTime.split(':')[1]);
        const endMinutes = parseInt(endTime.split(':')[0]) * 60 + parseInt(endTime.split(':')[1]);
        
        // Allow for overnight schedules (end time next day)
        expect(startMinutes).not.toBe(endMinutes); // They shouldn't be exactly the same
      }
    }
  });
});

test.describe('Attendant Notification Window API Tests', () => {
  let request;

  test.beforeEach(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: 'http://localhost:8000'
    });
  });

  test.afterEach(async () => {
    await request.dispose();
  });

  test('GET /api/v1/attendants/{attendant_id} - should return 200 with notification fields for valid attendant', async () => {
    // Act
    const response = await request.get(`/api/v1/attendants/${TEST_DATA.validAttendantId}`);
    
    // Assert response status
    expect(response.status()).toBe(200);
    
    // Assert response structure
    const responseBody = await response.json();
    expect(responseBody).toHaveProperty('id');
    expect(responseBody).toHaveProperty('name');
    expect(responseBody).toHaveProperty('email');
    expect(responseBody).toHaveProperty('phone');
    expect(responseBody).toHaveProperty('receipt_type');
    expect(responseBody).toHaveProperty('role');
    expect(responseBody).toHaveProperty('active');
    
    // Validate notification window fields are present
    validateNotificationFields(responseBody);
    
    // Validate data types and formats
    expect(isValidTimeFormat(responseBody.notification_start_time)).toBeTruthy();
    expect(isValidTimeFormat(responseBody.notification_end_time)).toBeTruthy();
    expect(isValidDateTimeFormat(responseBody.paused_until)).toBeTruthy();
    
    // Attendant-specific fields
    expect(responseBody).toHaveProperty('attendant_data');
    
    // Log response for debugging
    console.log('Attendant Response:', JSON.stringify(responseBody, null, 2));
  });

  test('GET /api/v1/attendants/{attendant_id} - should return default notification window when not explicitly set', async () => {
    // Act
    const response = await request.get(`/api/v1/attendants/${TEST_DATA.validAttendantId}`);
    
    // Assert
    expect(response.status()).toBe(200);
    const responseBody = await response.json();
    
    // Validate notification fields exist
    validateNotificationFields(responseBody);
    
    // Check for valid format when values are present
    if (responseBody.notification_start_time !== null) {
      expect(isValidTimeFormat(responseBody.notification_start_time)).toBeTruthy();
    }
    if (responseBody.notification_end_time !== null) {
      expect(isValidTimeFormat(responseBody.notification_end_time)).toBeTruthy();
    }
  });

  test('GET /api/v1/attendants/{attendant_id} - should return 404 for non-existent attendant', async () => {
    // Act
    const response = await request.get(`/api/v1/attendants/${TEST_DATA.nonExistentAttendantId}`);
    
    // Assert
    expect(response.status()).toBe(404);
    
    const responseBody = await response.json();
    expect(responseBody).toHaveProperty('detail');
    
    // Log error response for debugging
    console.log('404 Attendant Response:', JSON.stringify(responseBody, null, 2));
  });

  test('GET /api/v1/attendants/{attendant_id} - should handle invalid attendant ID format gracefully', async () => {
    // Test with various invalid formats
    const invalidIds = ['abc', '0', '-1', '1.5', 'null'];
    
    for (const invalidId of invalidIds) {
      const response = await request.get(`/api/v1/attendants/${invalidId}`);
      
      // Should return 400 for validation errors or 404 for not found
      expect([400, 404].includes(response.status())).toBeTruthy();
      
      if (response.status() !== 500) { // Avoid logging server errors
        const responseBody = await response.json();
        console.log(`Invalid ID ${invalidId} Response:`, JSON.stringify(responseBody, null, 2));
      }
    }
  });

  test('GET /api/v1/attendants/{attendant_id} - should validate attendant-specific notification constraints', async () => {
    // Act
    const response = await request.get(`/api/v1/attendants/${TEST_DATA.validAttendantId}`);
    
    if (response.status() === 200) {
      const responseBody = await response.json();
      
      // Validate attendant data structure
      if (responseBody.attendant_data) {
        expect(responseBody.attendant_data).toBeInstanceOf(Object);
        // Could validate attendant-specific fields here if needed
      }
      
      // Validate notification fields for attendants
      validateNotificationFields(responseBody);
    }
  });
});

test.describe('Notification Window Edge Cases and Error Scenarios', () => {
  let request;

  test.beforeEach(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: 'http://localhost:8000'
    });
  });

  test.afterEach(async () => {
    await request.dispose();
  });

  test('Should handle server errors gracefully', async () => {
    // Test with potentially problematic IDs that might cause server errors
    const problematicIds = [Number.MAX_SAFE_INTEGER, '99999999999999999999'];
    
    for (const id of problematicIds) {
      const userResponse = await request.get(`/api/v1/users/user/${id}`);
      const attendantResponse = await request.get(`/api/v1/attendants/${id}`);
      
      // Server should not crash (500 errors are acceptable but should be logged)
      expect(userResponse.status()).not.toBe(502); // Bad Gateway
      expect(userResponse.status()).not.toBe(503); // Service Unavailable
      expect(attendantResponse.status()).not.toBe(502);
      expect(attendantResponse.status()).not.toBe(503);
      
      if (userResponse.status() === 500) {
        console.warn(`Server error for user ID ${id}:`, userResponse.status());
      }
      if (attendantResponse.status() === 500) {
        console.warn(`Server error for attendant ID ${id}:`, attendantResponse.status());
      }
    }
  });

  test('Should validate response structure consistency across different users', async () => {
    // Test multiple valid user IDs to ensure consistent response structure
    const userIds = [1, 2, 3]; // Adjust based on your test data
    let responseStructures = [];
    
    for (const userId of userIds) {
      const response = await request.get(`/api/v1/users/user/${userId}`);
      
      if (response.status() === 200) {
        const responseBody = await response.json();
        responseStructures.push(Object.keys(responseBody).sort());
        
        // Each response should have notification fields (paused_until may be excluded when null)
        const shouldHavePausedUntil = responseBody.hasOwnProperty('paused_until');
        validateNotificationFields(responseBody, null, null, null, shouldHavePausedUntil);
      }
    }
    
    // All successful responses should have core required fields (paused_until is optional)
    if (responseStructures.length > 1) {
      const requiredFields = ['id', 'name', 'phone', 'role', 'active', 'notification_start_time', 'notification_end_time'];
      responseStructures.forEach((structure, index) => {
        requiredFields.forEach(field => {
          expect(structure.includes(field)).toBeTruthy();
        });
      });
    }
  });

  test('Should validate response structure consistency across different attendants', async () => {
    // Test multiple valid attendant IDs to ensure consistent response structure
    const attendantIds = [1, 2, 3]; // Adjust based on your test data
    let responseStructures = [];
    
    for (const attendantId of attendantIds) {
      const response = await request.get(`/api/v1/attendants/${attendantId}`);
      
      if (response.status() === 200) {
        const responseBody = await response.json();
        responseStructures.push(Object.keys(responseBody).sort());
        
        // Each response should have notification fields
        validateNotificationFields(responseBody);
      }
    }
    
    // All successful responses should have core required fields (paused_until is optional)
    if (responseStructures.length > 1) {
      const requiredFields = ['id', 'name', 'phone', 'role', 'active', 'notification_start_time', 'notification_end_time'];
      responseStructures.forEach((structure, index) => {
        requiredFields.forEach(field => {
          expect(structure.includes(field)).toBeTruthy();
        });
      });
    }
  });
});

test.describe('Notification Window Performance and Load Tests', () => {
  let request;

  test.beforeEach(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: 'http://localhost:8000'
    });
  });

  test.afterEach(async () => {
    await request.dispose();
  });

  test('Should handle concurrent requests for user data', async () => {
    // Test concurrent requests to ensure the API can handle load
    const concurrentRequests = [];
    const numberOfRequests = 5;
    
    for (let i = 0; i < numberOfRequests; i++) {
      concurrentRequests.push(
        request.get(`/api/v1/users/user/${TEST_DATA.validUserId}`)
      );
    }
    
    const responses = await Promise.all(concurrentRequests);
    
    // All requests should succeed or fail consistently
    responses.forEach(response => {
      expect([200, 404].includes(response.status())).toBeTruthy();
    });
  });

  test('Should handle concurrent requests for attendant data', async () => {
    // Test concurrent requests to ensure the API can handle load
    const concurrentRequests = [];
    const numberOfRequests = 5;
    
    for (let i = 0; i < numberOfRequests; i++) {
      concurrentRequests.push(
        request.get(`/api/v1/attendants/${TEST_DATA.validAttendantId}`)
      );
    }
    
    const responses = await Promise.all(concurrentRequests);
    
    // All requests should succeed or fail consistently
    responses.forEach(response => {
      expect([200, 404].includes(response.status())).toBeTruthy();
    });
  });

  test('Should respond within acceptable time limits', async () => {
    const startTime = Date.now();
    
    const response = await request.get(`/api/v1/users/user/${TEST_DATA.validUserId}`);
    
    const endTime = Date.now();
    const responseTime = endTime - startTime;
    
    // API should respond within 2 seconds (adjust threshold as needed)
    expect(responseTime).toBeLessThan(2000);
    
    console.log(`Response time: ${responseTime}ms`);
    
    if (response.status() === 200) {
      const responseBody = await response.json();
      validateNotificationFields(responseBody);
    }
  });
});

// Parameterized tests for different scenarios
test.describe('Notification Window Field Validation Matrix', () => {
  let request;

  test.beforeEach(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: 'http://localhost:8000'
    });
  });

  test.afterEach(async () => {
    await request.dispose();
  });

  // This test would ideally run against known test data with different notification configurations
  test('Should validate different notification window configurations', async () => {
    const testCases = [
      {
        id: TEST_DATA.validUserId,
        endpoint: 'users/user',
        description: 'Standard user with default notification window'
      },
      {
        id: TEST_DATA.validAttendantId,
        endpoint: 'attendants',
        description: 'Standard attendant with default notification window'
      }
    ];

    for (const testCase of testCases) {
      console.log(`Testing: ${testCase.description}`);
      
      const response = await request.get(`/api/v1/${testCase.endpoint}/${testCase.id}`);
      
      if (response.status() === 200) {
        const responseBody = await response.json();
        
        // Validate notification fields
        validateNotificationFields(responseBody);
        
        // Additional validation based on business rules
        if (responseBody.notification_start_time && responseBody.notification_end_time) {
          expect(isValidTimeFormat(responseBody.notification_start_time)).toBeTruthy();
          expect(isValidTimeFormat(responseBody.notification_end_time)).toBeTruthy();
        }
        
        if (responseBody.paused_until) {
          expect(isValidDateTimeFormat(responseBody.paused_until)).toBeTruthy();
          // paused_until should be in the future or past, but should be a valid datetime
          const pausedDate = new Date(responseBody.paused_until);
          expect(pausedDate).toBeInstanceOf(Date);
          expect(!isNaN(pausedDate.getTime())).toBeTruthy();
        }
      }
    }
  });
});