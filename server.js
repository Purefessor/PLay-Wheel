const WebSocket = require('ws');

const wss = new WebSocket.Server({ port: 8080 });

console.log('Server started on port 8080');

wss.on('connection', ws => {
    console.log('Client connected');

    ws.on('message', message => {
        // Broadcast the message to all connected clients
        wss.clients.forEach(client => {
            if (client !== ws && client.readyState === WebSocket.OPEN) {
                client.send(message);
            }
        });
    });

    ws.on('close', () => {
        console.log('Client disconnected');
    });

    ws.on('error', error => {
        console.error('WebSocket error:', error);
    });
});
