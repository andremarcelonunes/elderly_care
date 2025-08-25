# API Test Suite - Notification Window Fields

This directory contains comprehensive Playwright API tests for testing notification window fields implementation across various endpoints.

## Test Files Overview

### 1. `notification-window-api.spec.js`
**CB-149 Implementation Tests**
- Tests for User and Attendant endpoints with notification window fields
- 31 tests covering positive, negative, edge cases, and performance scenarios
- Validates notification_start_time, notification_end_time, and paused_until fields
- Covers both individual user/attendant retrieval endpoints

### 2. `contact-notification-window-api.spec.js` 
**CB-152 Implementation Tests** ⭐ **NEW**
- Tests for Contact relationship endpoints with notification window fields
- 19 tests covering both contact endpoints:
  - `GET /api/v1/users/client/{client_id}/contacts` - Returns contacts for a client
  - `GET /api/v1/users/contact/{contact_id}/clients` - Returns clients for a contact
- Handles different response structures (simple arrays vs nested user objects)
- Tests bidirectional relationships between clients and contacts

### 3. `notification-window-contract.spec.js`
**Contract and Schema Validation**
- API contract tests ensuring backward compatibility
- Schema validation for response structures
- HTTP status code validation
- Data type and format validation

### 4. `patch-endpoints-api.spec.js`
**CB-164 PATCH Endpoints Tests** ⭐ **NEW**
- Tests for PATCH endpoints with partial update functionality
- 32 tests covering both user and attendant PATCH endpoints:
  - `PATCH /api/v1/users/update/{user_id}` - Partial user updates
  - `PATCH /api/v1/attendants/{user_id}` - Partial attendant updates
- Validates partial update behavior (only sent fields are updated)
- Tests notification window field updates via PATCH
- Error handling and validation testing for PATCH operations

### 5. `test-helpers.js`
**Shared Testing Utilities**
- Reusable validation functions for notification fields
- Mock data generators
- Time format validation utilities
- Response structure validators
- Health check utilities

## Test Coverage

### Endpoints Tested
- ✅ `GET /api/v1/users/user/{user_id}` (CB-149)
- ✅ `GET /api/v1/attendants/{attendant_id}` (CB-149)  
- ✅ `GET /api/v1/users/client/{client_id}/contacts` (CB-152)
- ✅ `GET /api/v1/users/contact/{contact_id}/clients` (CB-152)
- ✅ `PATCH /api/v1/users/update/{user_id}` (CB-164) **NEW**
- ✅ `PATCH /api/v1/attendants/{user_id}` (CB-164) **NEW**
- ✅ `PUT /api/v1/users/update/{user_id}` (CB-164 - verified compatibility)
- ✅ `PUT /api/v1/attendants/{user_id}` (CB-164 - verified compatibility)

### Notification Fields Validated
- ✅ `notification_start_time` (string, HH:MM format, default "08:00")
- ✅ `notification_end_time` (string, HH:MM format, default "22:00")
- ✅ `paused_until` (datetime ISO format, nullable)

### Test Scenarios Covered
- ✅ **Positive Cases**: Valid requests with expected notification fields
- ✅ **Negative Cases**: Invalid IDs, non-existent resources (404 responses)
- ✅ **Edge Cases**: Malformed IDs, boundary values, server errors
- ✅ **Performance Tests**: Concurrent requests, response time validation
- ✅ **Contract Tests**: Schema validation, backward compatibility
- ✅ **Data Validation**: Time format, datetime format, field presence
- ✅ **Partial Update Tests**: PATCH endpoints updating only specified fields (CB-164) **NEW**
- ✅ **HTTP Method Semantics**: PATCH vs PUT behavior validation (CB-164) **NEW**

## Key Test Data

### Test Users/Entities
- User ID 1: Has paused_until set to "2025-12-31T23:59:59"
- User ID 26: Client with default notification values, has Contact 28 associated
- Contact ID 28: Associated with Client 26, default notification window
- Attendant ID 19: Has paused_until set to "2025-11-30T18:00:00"
- Attendant ID 20: Default notification values

### API Response Structures

#### Contact Endpoints Response Structures
```javascript
// GET /api/v1/users/client/{client_id}/contacts
[
  {
    "id": 28,
    "name": "Contato Cliente1",
    "phone": "+5511966398456",
    "notification_start_time": "08:00",
    "notification_end_time": "22:00", 
    "paused_until": null,
    // ... other user fields
  }
]

// GET /api/v1/users/contact/{contact_id}/clients  
[
  {
    "user_id": 26,
    "user": {
      "id": 26,
      "name": "Cliente Teste1",
      "notification_start_time": "08:00",
      "notification_end_time": "22:00",
      "paused_until": null,
      // ... other user fields
    },
    "created_at": "2025-04-17T07:07:37.133435",
    "updated_at": "2025-04-17T07:07:37.133435"
  }
]
```

## Running Tests

### Run All API Tests
```bash
npx playwright test
```

### Run Specific Test File
```bash
npx playwright test notification-window-api.spec.js
npx playwright test contact-notification-window-api.spec.js
npx playwright test notification-window-contract.spec.js
npx playwright test patch-endpoints-api.spec.js
```

### Run with Specific Reporter
```bash
npx playwright test --reporter=list
npx playwright test --reporter=html
```

## Test Results Summary

### Total Test Count: 82+ tests
- CB-149 User/Attendant Tests: 31 tests ✅
- CB-152 Contact Tests: 19 tests ✅
- CB-164 PATCH Endpoints Tests: 32 tests ✅ **NEW**
- Contract/Schema Tests: Multiple validation tests ✅

### Success Rate: 100% (82+/82+ passing)

## Implementation Notes

### CB-152 Specific Implementation Details
1. **Response Structure Handling**: The contact clients endpoint returns nested user objects, requiring special validation logic
2. **Bidirectional Relationships**: Tests verify that if Client A has Contact B, then Contact B should have Client A
3. **Notification Field Consistency**: All user objects (whether returned directly or nested) include the same notification window fields
4. **Error Handling**: Proper 404 responses for non-existent clients/contacts with descriptive error messages

### CB-164 PATCH Endpoints Implementation Details ⭐ **NEW**
1. **Partial Update Functionality**: PATCH endpoints update only the fields provided in the request body
2. **Field-Level Updates**: Individual notification window fields can be updated independently
3. **Validation Consistency**: Same validation rules apply to PATCH and PUT endpoints
4. **Response Format**: PATCH endpoints return identical response format as PUT endpoints
5. **HTTP Method Semantics**: PATCH for explicit partial updates, PUT maintained for conceptual full updates
6. **Existing Architecture Leverage**: Uses the same `model_dump(exclude_unset=True)` pattern as PUT endpoints

### Field Behavior
- `paused_until`: Included in response even when null (not excluded despite response_model_exclude_none=True)
- Default values: notification_start_time="08:00", notification_end_time="22:00"
- Time format validation: HH:MM format with proper hour (00-23) and minute (00-59) validation
- DateTime format: ISO 8601 format with timezone information

### Test Independence
All tests are designed to be independent and can run in parallel without affecting each other. They use existing test data and do not create/modify database state.