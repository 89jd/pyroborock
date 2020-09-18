const TuyaDevice = require('tuyapi');

const fs = require('fs')
const readline = require('readline');

const isFromPython = process.argv.length == 5;

device = null

function connectDevice({ip, id, key}, onConnected = null) {
  device = new TuyaDevice({
    ip: ip,
    id: id,
    key: key,
    version: 3.3});

  function onDataListener (data) {
    sendResponse('ready', { data: data})
    device.removeListener('data', onDataListener);
    if (onConnected) {      
      onConnected();
    }
  }
  device.on('data', onDataListener);

  device.on('error', error => {
    console.log('Error(js): ', error)
    sendResponse('error', JSON.stringify(error, Object.getOwnPropertyNames(error)))
  });

  device.on('connected', () => {;
    sendResponse('connected')
    console.log('Connected (js)')
  });

  device.on('disconnected', () => {
    sendResponse('disconnected')
  });
  

  device.find().then(() => {
    device.connect();
  });

  return device
}

function setDps({dps, value}) {
  device.on('data', data => {
    sendResponse('response', data)
  });

  device.set({
    dps: dps,
    set: value
  })
}

function disconnect() {
  device.disconnect()
}

function sendResponse(type, data) {
  const response = {
    'type': type
  }
  if (data) {
    response['data'] = data
  }
  if (isFromPython) {
    console.log('Node response: ' + JSON.stringify(response))
  }
  writeStream.write(JSON.stringify(response))
  writeStream.write('\n')
}

const readFunctions = {
  'connect': connectDevice,
  'disconnect': disconnect,
  'set': setDps
}

async function main(profileName) {
    writeStream = fs.createWriteStream(null, {fd: parseInt(process.argv[3])});
    writeStream.on('end', function() {
        console.log('Write stream finished');
    });
    writeStream.on('error', function(err) {
      console.log(err);
  });

    const lineReader = readline.createInterface({
      input: fs.createReadStream(null, {fd: parseInt(process.argv[2])})
    });

    // This catches any errors that happen while creating the readable stream (usually invalid names)
    lineReader.on('error', function(err) {
        console.log(err);
    });

    lineReader.on('line', function(data) {
        const msg = JSON.parse(data);
        console.log('Node receive: ' + data)
        f = readFunctions[msg['type']];
        if (f) {
          if ('data' in msg) {
            f(msg['data']);
          } else {
            f();
          }
        }
    });

    lineReader.on('end', function() {
        console.log('Read stream finished');
    });

    lineReader.on('error', function(err) {
        console.error(err);
    });
}

if (require.main === module) {
    console.log(process.argv.length);
    if (process.argv.length == 4) {
      main();
    } else {
      writeStream = process.stdout;
      var completed = false;
      connectDevice({ip: process.argv[2], id: process.argv[3], key: process.argv[4]},
        ()=>{
          if (!completed) {
            setDps({dps: process.argv[5], value: process.argv[6]})
            completed = true;
          }
        });
        setTimeout(()=>disconnect(), 2000);
    }
}