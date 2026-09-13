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
const pendingRequests = new Map();

function sendToOrville(method, params) {
    const id = Math.random().toString(36).substr(2, 9);
    const request = {
        type: 'request',
        id: id,
        method: method,
        params: params
    };
    console.log(JSON.stringify(request));
    
    return new Promise((resolve, reject) => {
        pendingRequests.set(id, { resolve, reject });
        setTimeout(() => {
            if (pendingRequests.has(id)) {
                pendingRequests.delete(id);
                reject(new Error(`Request ${id} timed out waiting for Orville response`));
            }
        }, 30000);
    });
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
        if (msg.type === 'response') {
            const pending = pendingRequests.get(msg.id);
            if (pending) {
                pendingRequests.delete(msg.id);
                if (msg.error) {
                    pending.reject(new Error(typeof msg.error === 'string' ? msg.error : JSON.stringify(msg.error)));
                } else {
                    pending.resolve(msg.result);
                }
            }
        } else if (msg.type === 'command') {
            const handler = global.orvilleCommands && global.orvilleCommands[msg.command];
            if (handler) {
                handler(msg.args);
            }
        }
    } catch (e) {
        // Ignore malformed lines
    }
});
