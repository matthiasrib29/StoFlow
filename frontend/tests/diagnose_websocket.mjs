#!/usr/bin/env node
/**
 * WebSocket Diagnosis Script - Node.js client
 *
 * Tests the WebSocket connection using the same socket.io-client
 * that the frontend uses.
 *
 * Run: node tests/diagnose_websocket.mjs
 *
 * Author: Claude
 * Date: 2026-01-19
 */

import { io } from 'socket.io-client'

const BACKEND_URL = 'http://localhost:8000'

// You need to provide a valid token - get it from browser localStorage
// or from the backend test
const TEST_TOKEN = process.env.TEST_TOKEN || null
const TEST_USER_ID = process.env.TEST_USER_ID || 1

function timestamp() {
  return new Date().toISOString().substr(11, 12)
}

function log(msg, data = null) {
  const ts = timestamp()
  if (data) {
    console.log(`[${ts}] ${msg}`, data)
  } else {
    console.log(`[${ts}] ${msg}`)
  }
}

class TestRunner {
  constructor() {
    this.results = []
  }

  async run(name, testFn) {
    console.log(`\n${'='.repeat(60)}`)
    console.log(`TEST: ${name}`)
    console.log('='.repeat(60))

    const start = Date.now()
    try {
      const result = await testFn()
      const duration = Date.now() - start

      if (result.passed) {
        console.log(`\n✅ PASS: ${name} (${duration}ms)`)
        console.log(`   ${result.message}`)
      } else {
        console.log(`\n❌ FAIL: ${name} (${duration}ms)`)
        console.log(`   ${result.message}`)
      }

      this.results.push({ name, ...result, duration })
      return result
    } catch (error) {
      const duration = Date.now() - start
      console.log(`\n❌ ERROR: ${name} (${duration}ms)`)
      console.log(`   ${error.message}`)
      this.results.push({ name, passed: false, message: error.message, duration })
      return { passed: false, message: error.message }
    }
  }

  summary() {
    console.log(`\n${'='.repeat(60)}`)
    console.log('SUMMARY')
    console.log('='.repeat(60))

    const passed = this.results.filter(r => r.passed).length
    const failed = this.results.length - passed

    console.log(`Total: ${this.results.length}`)
    console.log(`Passed: ${passed}`)
    console.log(`Failed: ${failed}`)

    if (failed > 0) {
      console.log('\n⚠️ FAILED TESTS:')
      this.results.filter(r => !r.passed).forEach(r => {
        console.log(`  - ${r.name}: ${r.message}`)
      })
    }
  }
}

// Test: WebSocket-only connection
async function testWebSocketOnly(token, userId) {
  return new Promise((resolve) => {
    const events = []
    let connected = false
    let disconnected = false
    let disconnectReason = null

    log('Creating socket with WebSocket-only transport...')

    const socket = io(BACKEND_URL, {
      auth: { token, user_id: userId },
      transports: ['websocket'],
      autoConnect: false,
      timeout: 10000,
      reconnection: false
    })

    socket.on('connect', () => {
      connected = true
      events.push({ event: 'connect', time: Date.now() })
      log('CONNECT', { id: socket.id, transport: socket.io.engine.transport.name })
    })

    socket.on('disconnect', (reason) => {
      disconnected = true
      disconnectReason = reason
      events.push({ event: 'disconnect', reason, time: Date.now() })
      log('DISCONNECT', { reason })
    })

    socket.on('connect_error', (err) => {
      events.push({ event: 'connect_error', error: err.message, time: Date.now() })
      log('CONNECT_ERROR', err.message)
    })

    // Connect
    socket.connect()

    // Wait 5 seconds then check
    setTimeout(() => {
      const stillConnected = socket.connected
      // Check BEFORE we disconnect ourselves
      const wasDisconnectedByServer = disconnected

      socket.disconnect()

      if (!connected) {
        resolve({ passed: false, message: 'Failed to connect', events })
      } else if (wasDisconnectedByServer) {
        resolve({
          passed: false,
          message: `Disconnected by server! Reason: ${disconnectReason}`,
          events,
          disconnectReason
        })
      } else if (stillConnected) {
        resolve({
          passed: true,
          message: 'Connected and stable for 5s',
          events
        })
      } else {
        resolve({
          passed: false,
          message: 'Unknown state',
          events
        })
      }
    }, 5000)
  })
}

// Test: Polling-only connection
async function testPollingOnly(token, userId) {
  return new Promise((resolve) => {
    const events = []
    let connected = false
    let disconnected = false
    let disconnectReason = null

    log('Creating socket with Polling-only transport...')

    const socket = io(BACKEND_URL, {
      auth: { token, user_id: userId },
      transports: ['polling'],
      autoConnect: false,
      timeout: 10000,
      reconnection: false
    })

    socket.on('connect', () => {
      connected = true
      events.push({ event: 'connect', time: Date.now() })
      log('CONNECT', { id: socket.id, transport: socket.io.engine.transport.name })
    })

    socket.on('disconnect', (reason) => {
      disconnected = true
      disconnectReason = reason
      events.push({ event: 'disconnect', reason, time: Date.now() })
      log('DISCONNECT', { reason })
    })

    socket.on('connect_error', (err) => {
      events.push({ event: 'connect_error', error: err.message, time: Date.now() })
      log('CONNECT_ERROR', err.message)
    })

    socket.connect()

    setTimeout(() => {
      const stillConnected = socket.connected
      const wasDisconnectedByServer = disconnected

      socket.disconnect()

      if (!connected) {
        resolve({ passed: false, message: 'Failed to connect', events })
      } else if (wasDisconnectedByServer) {
        resolve({
          passed: false,
          message: `Disconnected by server! Reason: ${disconnectReason}`,
          events
        })
      } else if (stillConnected) {
        resolve({
          passed: true,
          message: 'Connected and stable for 5s with polling',
          events
        })
      } else {
        resolve({
          passed: false,
          message: 'Unknown state',
          events
        })
      }
    }, 5000)
  })
}

// Test: Polling → WebSocket upgrade
async function testPollingToWebSocketUpgrade(token, userId) {
  return new Promise((resolve) => {
    const events = []
    let connected = false
    let disconnected = false
    let disconnectReason = null
    const transportHistory = []

    log('Creating socket with Polling → WebSocket upgrade...')
    log('(This is the scenario that was failing in the browser)')

    const socket = io(BACKEND_URL, {
      auth: { token, user_id: userId },
      transports: ['polling', 'websocket'],
      autoConnect: false,
      timeout: 10000,
      reconnection: false
    })

    socket.on('connect', () => {
      connected = true
      const transport = socket.io.engine.transport.name
      transportHistory.push({ transport, time: Date.now() })
      events.push({ event: 'connect', time: Date.now() })
      log('CONNECT', { id: socket.id, transport })
    })

    socket.on('disconnect', (reason) => {
      disconnected = true
      disconnectReason = reason
      events.push({ event: 'disconnect', reason, time: Date.now() })
      log('DISCONNECT', { reason })
    })

    socket.on('connect_error', (err) => {
      events.push({ event: 'connect_error', error: err.message, time: Date.now() })
      log('CONNECT_ERROR', err.message)
    })

    // Connect first, then attach engine listener
    socket.connect()

    // Listen for transport upgrade (must be after connect() call)
    socket.io.on('open', () => {
      socket.io.engine.on('upgrade', (transport) => {
        transportHistory.push({ transport: transport.name, time: Date.now() })
        log('TRANSPORT UPGRADE', transport.name)
      })
    })

    // Monitor for 10 seconds
    let checkCount = 0
    const interval = setInterval(() => {
      checkCount++
      if (!socket.connected) {
        clearInterval(interval)
        return
      }
      const currentTransport = socket.io.engine.transport.name
      log(`Second ${checkCount}: transport=${currentTransport}, connected=${socket.connected}`)
    }, 1000)

    setTimeout(() => {
      clearInterval(interval)
      const stillConnected = socket.connected
      const finalTransport = socket.io.engine?.transport?.name
      const wasDisconnectedByServer = disconnected

      socket.disconnect()

      if (!connected) {
        resolve({ passed: false, message: 'Failed to connect', events, transportHistory })
      } else if (wasDisconnectedByServer) {
        resolve({
          passed: false,
          message: `Disconnected by server! Reason: ${disconnectReason}`,
          events,
          transportHistory,
          disconnectReason
        })
      } else if (stillConnected) {
        resolve({
          passed: true,
          message: `Stable for 10s. Final transport: ${finalTransport}`,
          events,
          transportHistory
        })
      } else {
        resolve({
          passed: false,
          message: 'Unknown state',
          events,
          transportHistory
        })
      }
    }, 10000)
  })
}

// Test: Message emission
async function testMessageEmission(token, userId) {
  return new Promise((resolve) => {
    const events = []
    let connected = false
    let disconnected = false
    let disconnectReason = null

    log('Testing message emission...')

    const socket = io(BACKEND_URL, {
      auth: { token, user_id: userId },
      transports: ['websocket'],
      autoConnect: false,
      timeout: 10000,
      reconnection: false
    })

    socket.on('connect', () => {
      connected = true
      events.push({ event: 'connect', time: Date.now() })
      log('CONNECT', { id: socket.id })

      // Emit message after connect
      log('Emitting plugin_response...')
      socket.emit('plugin_response', {
        request_id: 'test_js_' + Date.now(),
        success: true,
        data: { test: 'from_node' },
        error: null
      })
      events.push({ event: 'emit', time: Date.now() })
    })

    socket.on('disconnect', (reason) => {
      disconnected = true
      disconnectReason = reason
      events.push({ event: 'disconnect', reason, time: Date.now() })
      log('DISCONNECT', { reason })
    })

    socket.on('connect_error', (err) => {
      events.push({ event: 'connect_error', error: err.message, time: Date.now() })
      log('CONNECT_ERROR', err.message)
    })

    socket.connect()

    setTimeout(() => {
      const stillConnected = socket.connected
      const wasDisconnectedByServer = disconnected

      socket.disconnect()

      if (!connected) {
        resolve({ passed: false, message: 'Failed to connect', events })
      } else if (wasDisconnectedByServer) {
        resolve({
          passed: false,
          message: `Disconnected by server after emit! Reason: ${disconnectReason}`,
          events
        })
      } else if (stillConnected) {
        resolve({
          passed: true,
          message: 'Emitted message, still connected',
          events
        })
      } else {
        resolve({
          passed: false,
          message: 'Unknown state',
          events
        })
      }
    }, 3000)
  })
}

// Main
async function main() {
  console.log('='.repeat(60))
  console.log('WEBSOCKET DIAGNOSTIC - Node.js Client')
  console.log(`Target: ${BACKEND_URL}`)
  console.log(`Time: ${new Date().toISOString()}`)
  console.log('='.repeat(60))

  // Check for token
  if (!TEST_TOKEN) {
    console.log('\n⚠️  No TEST_TOKEN provided!')
    console.log('Get a token from:')
    console.log('  1. Browser localStorage (access_token)')
    console.log('  2. Or run backend test to generate one')
    console.log('\nUsage: TEST_TOKEN=xxx TEST_USER_ID=1 node tests/diagnose_websocket.mjs')
    console.log('\nAlternatively, get token from backend:')
    console.log('  cd backend && source .venv/bin/activate')
    console.log('  python -c "from tests.websocket.diagnose_websocket import get_test_token; print(get_test_token()[0])"')
    process.exit(1)
  }

  log(`Using token (first 20 chars): ${TEST_TOKEN.substring(0, 20)}...`)
  log(`User ID: ${TEST_USER_ID}`)

  const runner = new TestRunner()

  await runner.run('WebSocket-only Connection', () => testWebSocketOnly(TEST_TOKEN, TEST_USER_ID))
  await runner.run('Polling-only Connection', () => testPollingOnly(TEST_TOKEN, TEST_USER_ID))
  await runner.run('Polling → WebSocket Upgrade', () => testPollingToWebSocketUpgrade(TEST_TOKEN, TEST_USER_ID))
  await runner.run('Message Emission', () => testMessageEmission(TEST_TOKEN, TEST_USER_ID))

  runner.summary()
}

main().catch(console.error)
