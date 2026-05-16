const { app, BrowserWindow } = require('electron')
const { spawn } = require('child_process')
const path = require('path')

let mainWindow
let flaskProcess

function startFlask() {
  flaskProcess = spawn('python', [
    path.join(__dirname, '..', 'main.py')
  ])
  flaskProcess.stdout.on('data', (data) => console.log(`Flask: ${data}`))
  flaskProcess.stderr.on('data', (data) => console.log(`Flask stderr: ${data}`))
}

const { session } = require('electron')

function clearSession() {
  session.defaultSession.clearStorageData({
    storages: ['cookies', 'localstorage', 'sessionstorage']
  })
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 750,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
    },
    icon: path.join(__dirname, 'logo.ico'),
    title: 'Access Guardians',
    autoHideMenuBar: true,
    titleBarStyle: 'hidden',
    titleBarOverlay: {
      color: '#0d0b14',
      symbolColor: '#a09bc0',
      height: 40,
    },
  })

  mainWindow.loadURL('http://127.0.0.1:5000')
  mainWindow.on('closed', () => { mainWindow = null })
}

app.whenReady().then(() => {
  clearSession()
  startFlask()
  setTimeout(createWindow, 2000)
})

app.on('window-all-closed', () => {
  const { execSync } = require('child_process')
  try {
    execSync('python encrypt_on_exit.py', {
      cwd: path.join(__dirname, '..')
    })
  } catch (e) {
    console.log('Encrypt error:', e.message)
  }
  if (flaskProcess) flaskProcess.kill()
  app.quit()
})
