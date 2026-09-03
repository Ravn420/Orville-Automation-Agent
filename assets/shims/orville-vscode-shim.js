/**
 * Orville VS Code Polyfill Shim
 * This script acts as the 'vscode' module for extensions running inside Orville.
 */

const readline = require('readline');
const fs = require('fs');
const path = require('path');

// --- The Polyfill ---
const vscode = {
    window: {
        showInformationMessage: async (message) => {
            return sendToOrville('window.showInformationMessage', { message });
        },
        showErrorMessage: async (message) => {
            return sendToOrville('window.showErrorMessage', { message });
        }
    },
    workspace: {
        fs: {
            readFile: async (uri) => {
                return sendToOrville('workspace.fs.readFile', { uri: uri.toString() });
            }
        }
    },
    commands: {
        registerCommand: (id, handler) => {
            global.orvilleCommands = global.orvilleCommands || {};
            global.orvilleCommands[id] = handler;
        }
    }
};

// --- Communication Layer ---
function sendToOrville(method, params) {
    const id = Math.random().toString(36).substr(2, 9);
    const request = {
        type: 'request',
        id: id,
        method: method,
        params: params
    };
    console.log(JSON.stringify(request));
    
    // In a real implementation, we would maintain a map of pending requests
    // and resolve promises when the response arrives from stdin.
    return Promise.resolve({ status: 'sent' });
}

// --- Extension Lifecycle ---
async function activateExtension(extensionPath) {
    try {
        const mainPath = path.join(extensionPath, 'main.js');
        if (fs.existsSync(mainPath)) {
            const extension = require(mainPath);
            if (extension.activate) {
                await extension.activate(vscode);
            }
        }
    } catch (e) {
        console.error(JSON.stringify({ type: 'error', message: e.message }));
    }
}

// --- Main Loop ---
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
});

const extensionPath = process.argv[2];
activateExtension(extensionPath);

rl.on('line', (line) => {
    try {
        const msg = JSON.parse(line);
        if (msg.type === 'command') {
            const handler = global.orvilleCommands && global.orvilleCommands[msg.command];
            if (handler) {
                handler(msg.args);
            }
        }
    } catch (e) {
        // Ignore malformed lines
    }
});
