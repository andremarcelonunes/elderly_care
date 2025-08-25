/**
 * Test Helper Utilities for Notification Window API Tests
 * Provides reusable functions for API testing scenarios
 */

/**
 * Validates that a response contains notification window fields when present
 * @param {Object} response - The API response object
 * @param {Object} expectedValues - Optional expected values for validation
 * @returns {Boolean} - Returns true if validation passes
 */
function validateNotificationFields(response, expectedValues = {}) {
  // Fields may be excluded when null due to response_model_exclude_none=True
  // So we only validate fields that are present
  
  // Validate expected values if provided and field is present
  if (expectedValues.notification_start_time !== undefined && response.hasOwnProperty('notification_start_time')) {
    if (response.notification_start_time !== expectedValues.notification_start_time) {
      throw new Error(`Expected notification_start_time to be ${expectedValues.notification_start_time}, got ${response.notification_start_time}`);
    }
  }
  
  if (expectedValues.notification_end_time !== undefined && response.hasOwnProperty('notification_end_time')) {
    if (response.notification_end_time !== expectedValues.notification_end_time) {
      throw new Error(`Expected notification_end_time to be ${expectedValues.notification_end_time}, got ${response.notification_end_time}`);
    }
  }
  
  if (expectedValues.paused_until !== undefined && response.hasOwnProperty('paused_until')) {
    if (response.paused_until !== expectedValues.paused_until) {
      throw new Error(`Expected paused_until to be ${expectedValues.paused_until}, got ${response.paused_until}`);
    }
  }
  
  // Validate formats if fields are present and not null
  if (response.hasOwnProperty('notification_start_time') && response.notification_start_time !== null) {
    if (!isValidTimeFormat(response.notification_start_time)) {
      throw new Error(`Invalid notification_start_time format: ${response.notification_start_time}`);
    }
  }
  
  if (response.hasOwnProperty('notification_end_time') && response.notification_end_time !== null) {
    if (!isValidTimeFormat(response.notification_end_time)) {
      throw new Error(`Invalid notification_end_time format: ${response.notification_end_time}`);
    }
  }
  
  if (response.hasOwnProperty('paused_until') && response.paused_until !== null) {
    if (!isValidDateTimeFormat(response.paused_until)) {
      throw new Error(`Invalid paused_until format: ${response.paused_until}`);
    }
  }
  
  return true;
}

/**
 * Validates time format (HH:MM)
 * @param {String} timeString - Time string to validate
 * @returns {Boolean} - Returns true if format is valid or if timeString is null/undefined
 */
function isValidTimeFormat(timeString) {
  if (timeString === null || timeString === undefined) {
    return true; // null/undefined is acceptable
  }
  
  if (typeof timeString !== 'string') {
    return false;
  }
  
  const timeRegex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/;
  return timeRegex.test(timeString);
}

/**
 * Validates datetime format (ISO 8601 or similar parseable format)
 * @param {String} dateTimeString - DateTime string to validate
 * @returns {Boolean} - Returns true if format is valid or if dateTimeString is null/undefined
 */
function isValidDateTimeFormat(dateTimeString) {
  if (dateTimeString === null || dateTimeString === undefined) {
    return true; // null/undefined is acceptable
  }
  
  if (typeof dateTimeString !== 'string') {
    return false;
  }
  
  const date = new Date(dateTimeString);
  return !isNaN(date.getTime());
}

/**
 * Validates that notification start time is before end time
 * @param {String} startTime - Start time in HH:MM format
 * @param {String} endTime - End time in HH:MM format
 * @returns {Boolean} - Returns true if start is before end, or if either is null
 */
function validateTimeWindow(startTime, endTime) {
  if (!startTime || !endTime) {
    return true; // Can't validate if either is null
  }
  
  if (!isValidTimeFormat(startTime) || !isValidTimeFormat(endTime)) {
    return false; // Invalid format
  }
  
  const startMinutes = timeStringToMinutes(startTime);
  const endMinutes = timeStringToMinutes(endTime);
  
  // Handle overnight schedules - if end time is smaller than start time,
  // assume it's the next day
  if (endMinutes < startMinutes) {
    // This could be valid for overnight schedules
    return true; // Allow overnight schedules
  }
  
  return startMinutes < endMinutes; // Normal case: start should be before end
}

/**
 * Converts time string (HH:MM) to minutes since midnight
 * @param {String} timeString - Time string in HH:MM format
 * @returns {Number} - Minutes since midnight
 */
function timeStringToMinutes(timeString) {
  const [hours, minutes] = timeString.split(':').map(Number);
  return hours * 60 + minutes;
}

/**
 * Creates a comprehensive test data set for API testing
 * @returns {Object} - Test data object with various scenarios
 */
function generateTestData() {
  return {
    validIds: {
      user: [1, 26, 2, 3, 4],  // Use actual existing user IDs from database - user 1 has paused_until set
      attendant: [19, 20, 32]  // Use actual existing attendant IDs from database - attendant 19 has paused_until set
    },
    invalidIds: {
      nonExistent: [999999, 888888, 777777],
      malformed: ['abc', '0', '-1', '1.5', 'null', '', ' ', 'undefined']
    },
    notificationTimes: {
      valid: ['00:00', '08:00', '12:30', '18:45', '23:59'],
      invalid: ['24:00', '25:30', '08:60', '8:00', '08:5', '', null]
    },
    dateTimeValues: {
      valid: [
        null,
        '2024-12-25T10:30:00Z',
        '2025-01-01T00:00:00.000Z',
        '2024-06-15T14:22:33+00:00'
      ],
      invalid: [
        'invalid-date',
        '2024-13-01T10:30:00Z',
        '2024-02-30T10:30:00Z',
        '24-12-25 10:30:00'
      ]
    }
  };
}

/**
 * Creates a mock response object for testing
 * @param {Object} overrides - Fields to override in the mock response
 * @returns {Object} - Mock response object
 */
function createMockUserResponse(overrides = {}) {
  return {
    id: 1,
    name: "Test User",
    email: "test@example.com",
    phone: "+1234567890",
    receipt_type: 1,
    role: "subscriber",
    active: true,
    notification_start_time: "08:00",
    notification_end_time: "22:00",
    paused_until: null,
    client_data: null,
    attendant_data: null,
    ...overrides
  };
}

/**
 * Creates a mock attendant response object for testing
 * @param {Object} overrides - Fields to override in the mock response
 * @returns {Object} - Mock attendant response object
 */
function createMockAttendantResponse(overrides = {}) {
  return {
    id: 1,
    name: "Dr. Test",
    email: "dr.test@example.com",
    phone: "+1234567890",
    receipt_type: 1,
    role: "attendant",
    active: true,
    notification_start_time: "09:00",
    notification_end_time: "18:00",
    paused_until: null,
    attendant_data: {
      cpf: "123.456.789-00",
      birthday: "1980-01-01",
      address: "123 Medical St",
      city: "Health City",
      state: "HC",
      code_address: "12345",
      registro_conselho: "CRM123456",
      nivel_experiencia: "senior",
      formacao: "Medicine",
      specialty_names: ["General Practice"],
      team_names: ["Team A"],
      function_names: "Doctor"
    },
    ...overrides
  };
}

/**
 * Validates the complete structure of a user response
 * @param {Object} response - The API response to validate
 * @returns {Boolean} - Returns true if structure is valid
 */
function validateUserResponseStructure(response) {
  const requiredFields = [
    'id', 'name', 'email', 'phone', 'receipt_type', 'role', 'active'
  ];
  
  const optionalFields = ['client_data', 'attendant_data', 'notification_start_time', 'notification_end_time', 'paused_until'];
  
  // Check required fields
  for (const field of requiredFields) {
    if (!response.hasOwnProperty(field)) {
      throw new Error(`Missing required field: ${field}`);
    }
  }
  
  // Validate data types
  if (typeof response.id !== 'number') {
    throw new Error(`Field 'id' should be a number, got ${typeof response.id}`);
  }
  
  if (typeof response.name !== 'string') {
    throw new Error(`Field 'name' should be a string, got ${typeof response.name}`);
  }
  
  if (typeof response.active !== 'boolean') {
    throw new Error(`Field 'active' should be a boolean, got ${typeof response.active}`);
  }
  
  // Validate notification fields if they are present (they may be excluded when null due to response_model_exclude_none=True)
  if (response.hasOwnProperty('notification_start_time') || 
      response.hasOwnProperty('notification_end_time') || 
      response.hasOwnProperty('paused_until')) {
    validateNotificationFields(response);
  }
  
  return true;
}

/**
 * Validates the complete structure of an attendant response
 * @param {Object} response - The API response to validate
 * @returns {Boolean} - Returns true if structure is valid
 */
function validateAttendantResponseStructure(response) {
  // First validate as a user response (attendants extend users)
  validateUserResponseStructure(response);
  
  // Then validate attendant-specific fields
  if (response.attendant_data && typeof response.attendant_data !== 'object') {
    throw new Error(`Field 'attendant_data' should be an object or null, got ${typeof response.attendant_data}`);
  }
  
  return true;
}

/**
 * Logs test results in a standardized format
 * @param {String} testName - Name of the test
 * @param {Object} response - API response object
 * @param {Number} statusCode - HTTP status code
 * @param {Number} responseTime - Response time in milliseconds
 */
function logTestResult(testName, response, statusCode, responseTime = null) {
  const timestamp = new Date().toISOString();
  let hasNotificationFields = 'NO';
  
  // Check if response has any notification fields
  if (response && (response.hasOwnProperty('notification_start_time') || 
                   response.hasOwnProperty('notification_end_time') || 
                   response.hasOwnProperty('paused_until'))) {
    try {
      validateNotificationFields(response, {});
      hasNotificationFields = 'YES';
    } catch (e) {
      hasNotificationFields = 'INVALID';
    }
  }
  
  const logEntry = {
    timestamp,
    test: testName,
    status: statusCode,
    responseTime: responseTime ? `${responseTime}ms` : 'N/A',
    hasNotificationFields: hasNotificationFields
  };
  
  console.log('Test Result:', JSON.stringify(logEntry, null, 2));
}

/**
 * Performs a health check on the API endpoints
 * @param {Object} request - Playwright request context
 * @returns {Object} - Health check results
 */
async function performHealthCheck(request) {
  const healthResults = {
    timestamp: new Date().toISOString(),
    endpoints: {}
  };
  
  const endpoints = [
    { path: '/api/v1/users/user/1', name: 'users' },
    { path: '/api/v1/attendants/1', name: 'attendants' }
  ];
  
  for (const endpoint of endpoints) {
    try {
      const startTime = Date.now();
      const response = await request.get(endpoint.path);
      const endTime = Date.now();
      
      healthResults.endpoints[endpoint.name] = {
        status: response.status(),
        responseTime: endTime - startTime,
        available: response.status() < 500
      };
    } catch (error) {
      healthResults.endpoints[endpoint.name] = {
        status: 'ERROR',
        responseTime: 'N/A',
        available: false,
        error: error.message
      };
    }
  }
  
  return healthResults;
}

// Export all functions for use in tests
module.exports = {
  validateNotificationFields,
  isValidTimeFormat,
  isValidDateTimeFormat,
  validateTimeWindow,
  timeStringToMinutes,
  generateTestData,
  createMockUserResponse,
  createMockAttendantResponse,
  validateUserResponseStructure,
  validateAttendantResponseStructure,
  logTestResult,
  performHealthCheck
};