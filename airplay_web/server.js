const http = require('http');
const fs = require('fs');
// safe routing module
const url = require('url');

const port = process.argv[2] || 8090;
let clients = [];

let currentMeta = { isPlaying: false, title: null, artist: null, album: null };
let currentCover = null;

const server = http.createServer((req, res) => {
    // allow cross-origin requests for web radio fetch
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    // handle preflight requests
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        return res.end();
    }

    // parse pathname to ignore potential query params
    const parsedUrl = url.parse(req.url).pathname;

    if (parsedUrl === '/stream') {
        res.writeHead(200, {
            'Content-Type': 'audio/mpeg',
            'Transfer-Encoding': 'chunked',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        });

        clients.push(res);

        req.on('close', () => {
            clients = clients.filter(c => c !== res);
        });

    } else if (parsedUrl === '/meta') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(currentMeta));

    } else if (parsedUrl === '/cover') {
        if (currentCover) {
            res.writeHead(200, { 'Content-Type': 'image/jpeg' });
            res.end(currentCover);
        } else {
            res.writeHead(404);
            res.end('No cover available');
        }

    } else {
        res.writeHead(200);
        res.end('AirPlay Web Stream running');
    }
});

process.stdin.on('data', chunk => {
    clients.forEach(client => client.write(chunk));
});

process.on('SIGTERM', () => process.exit(0));

server.listen(port, () => {
    console.log(`Server running on port ${port}`);
});

const parseMetadata = (xmlString) => {
    const codeMatch = xmlString.match(/<code>([0-9a-fA-F]+)<\/code>/);
    if (!codeMatch) return;
    
    const code = Buffer.from(codeMatch[1], 'hex').toString('utf8');
    
    // set playing state
    if (code === 'pbeg' || code === 'prsm') currentMeta.isPlaying = true;
    
    // pause without clearing metadata
    if (code === 'pfls') currentMeta.isPlaying = false;
    
    // clear metadata on disconnect or stream end
    if (code === 'pend') {
        currentMeta.isPlaying = false;
        currentMeta.title = null;
        currentMeta.artist = null;
        currentMeta.album = null;
        currentCover = null;
    }
    
    const dataMatch = xmlString.match(/<data encoding="base64">(.*?)<\/data>/s);
    if (!dataMatch) return;
    
    const data = Buffer.from(dataMatch[1].replace(/\s/g, ''), 'base64');
    
    // parse actual metadata
    if (code === 'minm') currentMeta.title = data.toString('utf8');
    if (code === 'asar') currentMeta.artist = data.toString('utf8');
    if (code === 'asal') currentMeta.album = data.toString('utf8');
    if (code === 'PICT') currentCover = data;
};

const readMetadataPipe = () => {
    if (!fs.existsSync('/tmp/shairport_metadata')) return setTimeout(readMetadataPipe, 1000);
    
    const stream = fs.createReadStream('/tmp/shairport_metadata');
    let buffer = "";
    
    stream.on('data', chunk => {
        buffer += chunk.toString('utf8');
        let start = buffer.indexOf('<item>');
        let end = buffer.indexOf('</item>');
        
        while (start !== -1 && end !== -1 && end > start) {
            parseMetadata(buffer.substring(start, end + 7));
            buffer = buffer.substring(end + 7);
            start = buffer.indexOf('<item>');
            end = buffer.indexOf('</item>');
        }
    });
    
    stream.on('end', () => setTimeout(readMetadataPipe, 1000));
    stream.on('error', () => setTimeout(readMetadataPipe, 1000));
};

readMetadataPipe();