// TypeScript - Command Injection Vulnerability
import { exec } from 'child_process';
import * as http from 'http';

const server = http.createServer((req, res) => {
    const url = new URL(req.url || '/', `http://${req.headers.host}`);
    const cmd = url.searchParams.get('cmd');

    // Vulnerability: Command Injection
    exec(cmd, (error, stdout, stderr) => {
        res.end(stdout);
    });
});

// Vulnerability: Prototype Pollution
function merge(target: any, source: any) {
    for (let key in source) {
        if (typeof source[key] === 'object') {
            target[key] = merge(target[key] || {}, source[key]);
        } else {
            target[key] = source[key];
        }
    }
    return target;
}

// Vulnerability: eval with user input
const userInput = '{"action": "alert(1)"}';
eval(userInput);

// Vulnerability: document.write in Node.js SSR
const userData = `<script>${userInput}</script>`;
// document.write(userData);

server.listen(3000);
