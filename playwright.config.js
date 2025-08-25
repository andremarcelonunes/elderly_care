// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright configuration for Backend Eldery API testing
 * Focus on notification window fields functionality (CB-149)
 */
module.exports = defineConfig({
  testDir: './backendeldery/tests/api',
  
  /* Run tests in files in parallel */
  fullyParallel: true,
  
  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,
  
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  
  /* Opt out of parallel tests on CI */
  workers: process.env.CI ? 1 : undefined,
  
  /* Reporter to use */
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results.json' }],
    ['junit', { outputFile: 'test-results.xml' }],
    ['line']
  ],
  
  /* Global test timeout */
  timeout: 30 * 1000,
  
  /* Global expect timeout */
  expect: {
    timeout: 10 * 1000,
  },
  
  /* Shared settings for all the projects below */
  use: {
    /* Base URL for API tests */
    baseURL: 'http://localhost:8000',
    
    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',
    
    /* API request context settings */
    extraHTTPHeaders: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
    
    /* Ignore HTTPS errors for development */
    ignoreHTTPSErrors: true,
  },

  /* Configure projects for different test types */
  projects: [
    {
      name: 'api-tests',
      testMatch: '**/*.spec.js',
      use: {
        ...devices['Desktop Chrome'],
        // API tests don't need browser context, but keeping for flexibility
        headless: true,
      },
    },
  ],

  /* Web server configuration for local development */
  webServer: {
    command: 'echo "Please ensure your FastAPI server is running on http://localhost:8000"',
    port: 8000,
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});