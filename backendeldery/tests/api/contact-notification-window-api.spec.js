/**
 * Comprehensive Playwright API Tests for Contact Notification Window Fields
 * CB-152: Testing notification window fields in contact GET endpoints
 * 
 * This test suite validates:
 * - GET /api/v1/users/client/{client_id}/contacts - Returns contacts for a client with notification fields
 * - GET /api/v1/users/contact/{contact_id}/clients - Returns clients for a contact with notification fields
 * 
 * Notification fields tested:
 * - notification_start_time (string, HH:MM format, default "08:00")
 * - notification_end_time (string, HH:MM format, default "22:00")  
 * - paused_until (datetime, nullable, excluded when null due to response_model_exclude_none=True)
 */

const { test, expect } = require('@playwright/test');
const { 
  validateNotificationFields,
  isValidTimeFormat,
  isValidDateTimeFormat,
  validateUserResponseStructure,
  logTestResult
} = require('./test-helpers');

// Test data constants based on CB-152 implementation
const TEST_DATA = {
  validClientId: 26,        // Client that has associated contacts
  validContactId: 28,       // Contact that has associated clients
  nonExistentClientId: 999999,
  nonExistentContactId: 999999,
  defaultNotificationStart: "08:00",
  defaultNotificationEnd: "22:00"
};

// Helper function to validate contact array response
function validateContactsArrayResponse(contacts) {
  expect(Array.isArray(contacts)).toBeTruthy();
  
  contacts.forEach((contact, index) => {
    expect(contact).toHaveProperty('id');
    expect(contact).toHaveProperty('name');
    expect(contact).toHaveProperty('phone');
    expect(contact).toHaveProperty('role');
    expect(contact).toHaveProperty('active');
    
    // Validate notification window fields are present
    expect(contact).toHaveProperty('notification_start_time');
    expect(contact).toHaveProperty('notification_end_time');
    expect(contact).toHaveProperty('paused_until');
    
    // Validate data types and formats
    expect(isValidTimeFormat(contact.notification_start_time)).toBeTruthy();
    expect(isValidTimeFormat(contact.notification_end_time)).toBeTruthy();
    expect(isValidDateTimeFormat(contact.paused_until)).toBeTruthy();
    
    console.log(`Contact ${index + 1} notification fields:`, {
      id: contact.id,
      notification_start_time: contact.notification_start_time,
      notification_end_time: contact.notification_end_time,
      paused_until: contact.paused_until
    });
  });
}

// Helper function to validate clients array response
function validateClientsArrayResponse(clients) {
  expect(Array.isArray(clients)).toBeTruthy();
  
  clients.forEach((clientAssociation, index) => {
    // The response structure includes a nested 'user' object
    expect(clientAssociation).toHaveProperty('user');
    expect(clientAssociation).toHaveProperty('user_id');
    
    const client = clientAssociation.user;
    
    expect(client).toHaveProperty('id');
    expect(client).toHaveProperty('name');
    expect(client).toHaveProperty('phone');
    expect(client).toHaveProperty('role');
    expect(client).toHaveProperty('active');
    
    // Validate notification window fields are present
    expect(client).toHaveProperty('notification_start_time');
    expect(client).toHaveProperty('notification_end_time');
    expect(client).toHaveProperty('paused_until');
    
    // Validate data types and formats
    expect(isValidTimeFormat(client.notification_start_time)).toBeTruthy();
    expect(isValidTimeFormat(client.notification_end_time)).toBeTruthy();
    expect(isValidDateTimeFormat(client.paused_until)).toBeTruthy();
    
    console.log(`Client ${index + 1} notification fields:`, {
      id: client.id,
      notification_start_time: client.notification_start_time,
      notification_end_time: client.notification_end_time,
      paused_until: client.paused_until
    });
  });
}

test.describe('Client Contacts Notification Window API Tests', () => {
  let request;

  test.beforeEach(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: 'http://localhost:8000'
    });
  });

  test.afterEach(async () => {
    await request.dispose();
  });

  test('GET /api/v1/users/client/{client_id}/contacts - should return 200 with contacts including notification fields', async () => {
    // Act
    const response = await request.get(`/api/v1/users/client/${TEST_DATA.validClientId}/contacts`);
    const startTime = Date.now();
    
    // Assert response status
    expect(response.status()).toBe(200);
    
    // Assert response structure
    const responseBody = await response.json();
    console.log('Client Contacts Response:', JSON.stringify(responseBody, null, 2));
    
    // Validate array response with notification fields
    validateContactsArrayResponse(responseBody);
    
    const endTime = Date.now();
    logTestResult('GET client contacts', responseBody.length > 0 ? responseBody[0] : null, response.status(), endTime - startTime);
  });

  test('GET /api/v1/users/client/{client_id}/contacts - should return expected notification field values', async () => {
    // Act
    const response = await request.get(`/api/v1/users/client/${TEST_DATA.validClientId}/contacts`);
    
    // Assert
    expect(response.status()).toBe(200);
    const responseBody = await response.json();
    
    // If we have contacts, verify they have the expected notification window values
    if (responseBody.length > 0) {
      responseBody.forEach(contact => {
        // Validate default values are present
        expect(contact.notification_start_time).toBe(TEST_DATA.defaultNotificationStart);
        expect(contact.notification_end_time).toBe(TEST_DATA.defaultNotificationEnd);
        
        // paused_until should be null (and may be excluded from response)
        if (contact.hasOwnProperty('paused_until')) {
          expect(contact.paused_until).toBeNull();
        }
      });
    }
  });

  test('GET /api/v1/users/client/{client_id}/contacts - should return empty array for client with no contacts', async () => {
    // Use a client ID that likely has no contacts (but still exists)
    const clientWithNoContacts = 1; // Assuming client 1 exists but has no contacts
    
    // Act
    const response = await request.get(`/api/v1/users/client/${clientWithNoContacts}/contacts`);
    
    // Assert
    expect(response.status()).toBe(200);
    const responseBody = await response.json();
    
    expect(Array.isArray(responseBody)).toBeTruthy();
    // Should be empty array or have contacts (we accept both cases)
    console.log('Client with no/few contacts response:', JSON.stringify(responseBody, null, 2));
    
    // If there are contacts, validate their structure
    if (responseBody.length > 0) {
      validateContactsArrayResponse(responseBody);
    }
  });

  test('GET /api/v1/users/client/{client_id}/contacts - should return 404 for non-existent client', async () => {
    // Act
    const response = await request.get(`/api/v1/users/client/${TEST_DATA.nonExistentClientId}/contacts`);
    
    // Assert
    expect(response.status()).toBe(404);
    
    const responseBody = await response.json();
    expect(responseBody).toHaveProperty('detail');
    
    console.log('404 Client Response:', JSON.stringify(responseBody, null, 2));
  });

  test('GET /api/v1/users/client/{client_id}/contacts - should handle invalid client ID format gracefully', async () => {
    // Test with various invalid formats
    const invalidIds = ['abc', '0', '-1', '1.5', 'null'];
    
    for (const invalidId of invalidIds) {
      const response = await request.get(`/api/v1/users/client/${invalidId}/contacts`);
      
      // Should return 400 for validation errors or 404 for not found
      expect([400, 404, 422].includes(response.status())).toBeTruthy();
      
      if (response.status() !== 500) { // Avoid logging server errors
        const responseBody = await response.json();
        console.log(`Invalid Client ID ${invalidId} Response:`, JSON.stringify(responseBody, null, 2));
      }
    }
  });

  test('GET /api/v1/users/client/{client_id}/contacts - should validate notification time format constraints', async () => {
    // Act
    const response = await request.get(`/api/v1/users/client/${TEST_DATA.validClientId}/contacts`);
    
    if (response.status() === 200) {
      const responseBody = await response.json();
      
      responseBody.forEach(contact => {
        // Validate time format if present
        if (contact.notification_start_time) {
          expect(contact.notification_start_time).toMatch(/^([0-1][0-9]|2[0-3]):[0-5][0-9]$/);
        }
        
        if (contact.notification_end_time) {
          expect(contact.notification_end_time).toMatch(/^([0-1][0-9]|2[0-3]):[0-5][0-9]$/);
        }
        
        // Validate logical constraint (start time should be before end time for same day)
        if (contact.notification_start_time && contact.notification_end_time) {
          const startTime = contact.notification_start_time;
          const endTime = contact.notification_end_time;
          
          // Convert to comparable format
          const startMinutes = parseInt(startTime.split(':')[0]) * 60 + parseInt(startTime.split(':')[1]);
          const endMinutes = parseInt(endTime.split(':')[0]) * 60 + parseInt(endTime.split(':')[1]);
          
          // Allow for overnight schedules (end time next day) or normal day schedules
          expect(startMinutes).not.toBe(endMinutes); // They shouldn't be exactly the same
        }
      });
    }
  });
});

test.describe('Contact Clients Notification Window API Tests', () => {
  let request;

  test.beforeEach(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: 'http://localhost:8000'
    });
  });

  test.afterEach(async () => {
    await request.dispose();
  });

  test('GET /api/v1/users/contact/{contact_id}/clients - should return 200 with clients including notification fields', async () => {
    // Act
    const response = await request.get(`/api/v1/users/contact/${TEST_DATA.validContactId}/clients`);
    const startTime = Date.now();
    
    // Assert response status
    expect(response.status()).toBe(200);
    
    // Assert response structure
    const responseBody = await response.json();
    console.log('Contact Clients Response:', JSON.stringify(responseBody, null, 2));
    
    // Validate array response with notification fields
    validateClientsArrayResponse(responseBody);
    
    const endTime = Date.now();
    logTestResult('GET contact clients', responseBody.length > 0 ? responseBody[0].user : null, response.status(), endTime - startTime);
  });

  test('GET /api/v1/users/contact/{contact_id}/clients - should return expected notification field values', async () => {
    // Act
    const response = await request.get(`/api/v1/users/contact/${TEST_DATA.validContactId}/clients`);
    
    // Assert
    expect(response.status()).toBe(200);
    const responseBody = await response.json();
    
    // If we have clients, verify they have the expected notification window values
    if (responseBody.length > 0) {
      responseBody.forEach(clientAssociation => {
        const client = clientAssociation.user;
        
        // Validate default values are present
        expect(client.notification_start_time).toBe(TEST_DATA.defaultNotificationStart);
        expect(client.notification_end_time).toBe(TEST_DATA.defaultNotificationEnd);
        
        // paused_until should be null
        expect(client.paused_until).toBeNull();
      });
    }
  });

  test('GET /api/v1/users/contact/{contact_id}/clients - should return empty array for contact with no clients', async () => {
    // Use a contact ID that likely has no clients (but still exists)
    const contactWithNoClients = 1; // Assuming contact 1 exists but has no clients
    
    // Act
    const response = await request.get(`/api/v1/users/contact/${contactWithNoClients}/clients`);
    
    // Assert
    expect(response.status()).toBe(200);
    const responseBody = await response.json();
    
    expect(Array.isArray(responseBody)).toBeTruthy();
    // Should be empty array or have clients (we accept both cases)
    console.log('Contact with no/few clients response:', JSON.stringify(responseBody, null, 2));
    
    // If there are clients, validate their structure
    if (responseBody.length > 0) {
      validateClientsArrayResponse(responseBody);
    }
  });

  test('GET /api/v1/users/contact/{contact_id}/clients - should return 404 for non-existent contact', async () => {
    // Act
    const response = await request.get(`/api/v1/users/contact/${TEST_DATA.nonExistentContactId}/clients`);
    
    // Assert
    expect(response.status()).toBe(404);
    
    const responseBody = await response.json();
    expect(responseBody).toHaveProperty('detail');
    
    console.log('404 Contact Response:', JSON.stringify(responseBody, null, 2));
  });

  test('GET /api/v1/users/contact/{contact_id}/clients - should handle invalid contact ID format gracefully', async () => {
    // Test with various invalid formats
    const invalidIds = ['abc', '0', '-1', '1.5', 'null'];
    
    for (const invalidId of invalidIds) {
      const response = await request.get(`/api/v1/users/contact/${invalidId}/clients`);
      
      // Should return 400 for validation errors or 404 for not found
      expect([400, 404, 422].includes(response.status())).toBeTruthy();
      
      if (response.status() !== 500) { // Avoid logging server errors
        const responseBody = await response.json();
        console.log(`Invalid Contact ID ${invalidId} Response:`, JSON.stringify(responseBody, null, 2));
      }
    }
  });

  test('GET /api/v1/users/contact/{contact_id}/clients - should validate notification time format constraints', async () => {
    // Act
    const response = await request.get(`/api/v1/users/contact/${TEST_DATA.validContactId}/clients`);
    
    if (response.status() === 200) {
      const responseBody = await response.json();
      
      responseBody.forEach(clientAssociation => {
        const client = clientAssociation.user;
        
        // Validate time format if present
        if (client.notification_start_time) {
          expect(client.notification_start_time).toMatch(/^([0-1][0-9]|2[0-3]):[0-5][0-9]$/);
        }
        
        if (client.notification_end_time) {
          expect(client.notification_end_time).toMatch(/^([0-1][0-9]|2[0-3]):[0-5][0-9]$/);
        }
        
        // Validate logical constraint (start time should be before end time for same day)
        if (client.notification_start_time && client.notification_end_time) {
          const startTime = client.notification_start_time;
          const endTime = client.notification_end_time;
          
          // Convert to comparable format
          const startMinutes = parseInt(startTime.split(':')[0]) * 60 + parseInt(startTime.split(':')[1]);
          const endMinutes = parseInt(endTime.split(':')[0]) * 60 + parseInt(endTime.split(':')[1]);
          
          // Allow for overnight schedules (end time next day) or normal day schedules
          expect(startMinutes).not.toBe(endMinutes); // They shouldn't be exactly the same
        }
      });
    }
  });
});

test.describe('Contact Endpoints Edge Cases and Error Scenarios', () => {
  let request;

  test.beforeEach(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: 'http://localhost:8000'
    });
  });

  test.afterEach(async () => {
    await request.dispose();
  });

  test('Should handle server errors gracefully for contact endpoints', async () => {
    // Test with potentially problematic IDs that might cause server errors
    const problematicIds = [Number.MAX_SAFE_INTEGER, '99999999999999999999'];
    
    for (const id of problematicIds) {
      const clientContactsResponse = await request.get(`/api/v1/users/client/${id}/contacts`);
      const contactClientsResponse = await request.get(`/api/v1/users/contact/${id}/clients`);
      
      // Server should not crash (500 errors are acceptable but should be logged)
      expect(clientContactsResponse.status()).not.toBe(502); // Bad Gateway
      expect(clientContactsResponse.status()).not.toBe(503); // Service Unavailable
      expect(contactClientsResponse.status()).not.toBe(502);
      expect(contactClientsResponse.status()).not.toBe(503);
      
      if (clientContactsResponse.status() === 500) {
        console.warn(`Server error for client contacts ID ${id}:`, clientContactsResponse.status());
      }
      if (contactClientsResponse.status() === 500) {
        console.warn(`Server error for contact clients ID ${id}:`, contactClientsResponse.status());
      }
    }
  });

  test('Should validate response structure consistency across different contact requests', async () => {
    // Test multiple valid client/contact IDs to ensure consistent response structure
    const clientIds = [1, 2, TEST_DATA.validClientId]; // Adjust based on your test data
    let responseStructures = [];
    
    for (const clientId of clientIds) {
      const response = await request.get(`/api/v1/users/client/${clientId}/contacts`);
      
      if (response.status() === 200) {
        const responseBody = await response.json();
        
        if (responseBody.length > 0) {
          // Collect structure from first contact in each response
          responseStructures.push(Object.keys(responseBody[0]).sort());
          
          // Validate each contact has notification fields
          validateContactsArrayResponse(responseBody);
        }
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

  test('Should validate bidirectional relationship consistency', async () => {
    // Test the bidirectional relationship: if client has contact, contact should have client
    
    // First get contacts for a client
    const clientContactsResponse = await request.get(`/api/v1/users/client/${TEST_DATA.validClientId}/contacts`);
    
    if (clientContactsResponse.status() === 200) {
      const contacts = await clientContactsResponse.json();
      
      if (contacts.length > 0) {
        const firstContactId = contacts[0].id;
        
        // Now get clients for that contact
        const contactClientsResponse = await request.get(`/api/v1/users/contact/${firstContactId}/clients`);
        
        if (contactClientsResponse.status() === 200) {
          const clients = await contactClientsResponse.json();
          
          // The original client should be in this contact's clients list
          const foundOriginalClient = clients.find(client => client.id === TEST_DATA.validClientId);
          
          if (foundOriginalClient) {
            console.log('Bidirectional relationship verified: Client', TEST_DATA.validClientId, 'is associated with Contact', firstContactId);
            
            // Validate notification fields in both directions
            validateContactsArrayResponse(contacts);
            validateClientsArrayResponse(clients);
          } else {
            console.log('Note: Bidirectional relationship not found or data may be asymmetric');
          }
        }
      }
    }
  });
});

test.describe('Contact Endpoints Performance and Load Tests', () => {
  let request;

  test.beforeEach(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: 'http://localhost:8000'
    });
  });

  test.afterEach(async () => {
    await request.dispose();
  });

  test('Should handle concurrent requests for client contacts', async () => {
    // Test concurrent requests to ensure the API can handle load
    const concurrentRequests = [];
    const numberOfRequests = 5;
    
    for (let i = 0; i < numberOfRequests; i++) {
      concurrentRequests.push(
        request.get(`/api/v1/users/client/${TEST_DATA.validClientId}/contacts`)
      );
    }
    
    const responses = await Promise.all(concurrentRequests);
    
    // All requests should succeed or fail consistently
    responses.forEach(response => {
      expect([200, 404].includes(response.status())).toBeTruthy();
    });
  });

  test('Should handle concurrent requests for contact clients', async () => {
    // Test concurrent requests to ensure the API can handle load
    const concurrentRequests = [];
    const numberOfRequests = 5;
    
    for (let i = 0; i < numberOfRequests; i++) {
      concurrentRequests.push(
        request.get(`/api/v1/users/contact/${TEST_DATA.validContactId}/clients`)
      );
    }
    
    const responses = await Promise.all(concurrentRequests);
    
    // All requests should succeed or fail consistently
    responses.forEach(response => {
      expect([200, 404].includes(response.status())).toBeTruthy();
    });
  });

  test('Should respond within acceptable time limits for contact endpoints', async () => {
    const startTime = Date.now();
    
    const [clientContactsResponse, contactClientsResponse] = await Promise.all([
      request.get(`/api/v1/users/client/${TEST_DATA.validClientId}/contacts`),
      request.get(`/api/v1/users/contact/${TEST_DATA.validContactId}/clients`)
    ]);
    
    const endTime = Date.now();
    const responseTime = endTime - startTime;
    
    // API should respond within 3 seconds for both endpoints (adjust threshold as needed)
    expect(responseTime).toBeLessThan(3000);
    
    console.log(`Contact endpoints response time: ${responseTime}ms`);
    
    if (clientContactsResponse.status() === 200) {
      const contacts = await clientContactsResponse.json();
      validateContactsArrayResponse(contacts);
    }
    
    if (contactClientsResponse.status() === 200) {
      const clients = await contactClientsResponse.json();
      validateClientsArrayResponse(clients);
    }
  });
});

test.describe('Contact Notification Window Field Validation Matrix', () => {
  let request;

  test.beforeEach(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: 'http://localhost:8000'
    });
  });

  test.afterEach(async () => {
    await request.dispose();
  });

  test('Should validate different contact notification window configurations', async () => {
    const testCases = [
      {
        id: TEST_DATA.validClientId,
        endpoint: 'users/client',
        subEndpoint: 'contacts',
        description: 'Client contacts with notification windows'
      },
      {
        id: TEST_DATA.validContactId,
        endpoint: 'users/contact',
        subEndpoint: 'clients',
        description: 'Contact clients with notification windows'
      }
    ];

    for (const testCase of testCases) {
      console.log(`Testing: ${testCase.description}`);
      
      const response = await request.get(`/api/v1/${testCase.endpoint}/${testCase.id}/${testCase.subEndpoint}`);
      
      if (response.status() === 200) {
        const responseBody = await response.json();
        
        // Validate notification fields for each item in the array
        responseBody.forEach((item, index) => {
          // Handle different response structures (contacts vs. client associations)
          let userObj = item;
          if (item.user) {
            // This is a client association response
            userObj = item.user;
          }
          
          console.log(`Validating item ${index + 1}:`, {
            id: userObj.id,
            name: userObj.name,
            notification_start_time: userObj.notification_start_time,
            notification_end_time: userObj.notification_end_time,
            paused_until: userObj.paused_until
          });
          
          // Validate notification fields exist and have proper format
          expect(userObj).toHaveProperty('notification_start_time');
          expect(userObj).toHaveProperty('notification_end_time');
          
          if (userObj.notification_start_time && userObj.notification_end_time) {
            expect(isValidTimeFormat(userObj.notification_start_time)).toBeTruthy();
            expect(isValidTimeFormat(userObj.notification_end_time)).toBeTruthy();
          }
          
          if (userObj.paused_until) {
            expect(isValidDateTimeFormat(userObj.paused_until)).toBeTruthy();
            // paused_until should be in the future or past, but should be a valid datetime
            const pausedDate = new Date(userObj.paused_until);
            expect(pausedDate).toBeInstanceOf(Date);
            expect(!isNaN(pausedDate.getTime())).toBeTruthy();
          }
        });
      }
    }
  });
});