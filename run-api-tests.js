#!/usr/bin/env node

/**
 * API Test Runner Script
 * Simplified script to run Playwright API tests for notification window functionality
 */

const { spawn } = require('child_process');
const path = require('path');

// Color codes for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function checkServerHealth() {
  return new Promise((resolve) => {
    const http = require('http');
    const options = {
      hostname: 'localhost',
      port: 8000,
      path: '/docs',
      method: 'GET',
      timeout: 5000
    };

    const req = http.request(options, (res) => {
      resolve(res.statusCode === 200);
    });

    req.on('error', () => {
      resolve(false);
    });

    req.on('timeout', () => {
      req.abort();
      resolve(false);
    });

    req.end();
  });
}

async function runTests(testOptions = []) {
  log('\n🧪 Starting Playwright API Tests for Notification Window Fields', 'cyan');
  log('================================================================', 'cyan');

  // Check if server is running
  log('\n🔍 Checking if FastAPI server is running...', 'yellow');
  const serverHealthy = await checkServerHealth();
  
  if (!serverHealthy) {
    log('❌ FastAPI server is not running on http://localhost:8000', 'red');
    log('Please start the server with: poetry run uvicorn backendeldery.main:app --reload --port 8000', 'yellow');
    process.exit(1);
  }
  
  log('✅ FastAPI server is running', 'green');

  // Default test command
  const defaultArgs = [
    'playwright',
    'test',
    'backendeldery/tests/api/',
    '--reporter=line'
  ];

  const args = testOptions.length > 0 ? ['playwright', 'test', ...testOptions] : defaultArgs;

  log(`\n🚀 Running command: npx ${args.join(' ')}`, 'blue');
  log('================================================================', 'cyan');

  const testProcess = spawn('npx', args, {
    stdio: 'inherit',
    cwd: process.cwd()
  });

  testProcess.on('close', (code) => {
    log('\n================================================================', 'cyan');
    if (code === 0) {
      log('✅ All tests passed successfully!', 'green');
    } else {
      log('❌ Some tests failed. Check the output above for details.', 'red');
      log('\n💡 Debug tips:', 'yellow');
      log('  - Run with --headed to see browser actions', 'yellow');
      log('  - Run with --debug to step through tests', 'yellow');
      log('  - Check server logs for API errors', 'yellow');
    }
    log('================================================================', 'cyan');
    process.exit(code);
  });

  testProcess.on('error', (error) => {
    log(`❌ Error running tests: ${error.message}`, 'red');
    process.exit(1);
  });
}

// Parse command line arguments
const args = process.argv.slice(2);

// Help text
if (args.includes('--help') || args.includes('-h')) {
  log('\n🧪 API Test Runner for Notification Window Fields', 'cyan');
  log('===============================================', 'cyan');
  log('\nUsage: node run-api-tests.js [options]', 'bright');
  log('\nOptions:', 'bright');
  log('  --help, -h          Show this help message', 'white');
  log('  --headed           Run tests in headed mode (show browser)', 'white');
  log('  --debug            Run tests in debug mode', 'white');
  log('  --ui               Run tests in UI mode', 'white');
  log('  --reporter=<type>  Specify reporter (html, json, line)', 'white');
  log('  --grep=<pattern>   Run only tests matching pattern', 'white');
  log('  --contract         Run only contract tests', 'white');
  log('  --api              Run only main API tests', 'white');
  log('  --verbose          Show verbose output', 'white');
  log('\nExamples:', 'bright');
  log('  node run-api-tests.js                    # Run all API tests', 'yellow');
  log('  node run-api-tests.js --headed           # Run with browser visible', 'yellow');
  log('  node run-api-tests.js --debug            # Run in debug mode', 'yellow');
  log('  node run-api-tests.js --contract         # Run only contract tests', 'yellow');
  log('  node run-api-tests.js --grep="user"      # Run only tests with "user" in name', 'yellow');
  log('  node run-api-tests.js --reporter=html    # Generate HTML report', 'yellow');
  log('');
  process.exit(0);
}

// Handle specific test options
let testOptions = [];

// Handle contract-only tests
if (args.includes('--contract')) {
  testOptions.push('backendeldery/tests/api/notification-window-contract.spec.js');
  args.splice(args.indexOf('--contract'), 1);
}

// Handle main API tests only
if (args.includes('--api')) {
  testOptions.push('backendeldery/tests/api/notification-window-api.spec.js');
  args.splice(args.indexOf('--api'), 1);
}

// Add remaining args to test options
testOptions.push(...args);

// Run the tests
runTests(testOptions).catch((error) => {
  log(`❌ Unexpected error: ${error.message}`, 'red');
  process.exit(1);
});